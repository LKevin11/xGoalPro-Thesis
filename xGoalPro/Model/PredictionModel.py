import joblib

from Persistence.Api import IApi
import aiohttp
from datetime import date
from dateutil.relativedelta import relativedelta
import asyncio
import numpy as np
from scipy.stats import poisson
import warnings
from typing import Optional, Tuple, Any

from Persistence.StorageInterface import IPredictionStorage

from ResourcePath import resource_path


class PredictionModel:
    """A model for football match predictions using machine learning and API data.

    This model interacts with an API to fetch leagues, teams, matches, and head-to-head data,
    calculates team statistics, and uses trained ML models to predict match outcomes. 
    Predictions are stored in a persistence storage interface.

    Attributes:
        __api (IApi): API interface for fetching leagues, teams, and match data.
        __storage (IPredictionStorage): Storage interface for storing and retrieving predictions.
        __ml_models (dict): Dictionary of machine learning models for predicting scores.
        __leagues (list): List of league codes to include when fetching competitions.
    """

    def __init__(self, api, storage, ml_models):
        """Initialize PredictionModel with API, storage, and ML models.

        Args:
            api (IApi): API interface for football data.
            storage (IPredictionStorage): Storage interface for predictions and team data.
            ml_models (dict): Dictionary of ML models for home/away predictions.
        """
        self.__api: IApi = api
        self.__storage: IPredictionStorage = storage
        self.__ml_models: dict = ml_models
        self.__leagues: list = []

    def add_league(self, league_code: str) -> None:
        """Add a league code to the list of leagues for fetching competitions.

        Args:
            league_code (str): League code (e.g., 'PL' for Premier League).
        """
        self.__leagues.append(league_code)

    async def fetch_leagues(self) -> Optional[Tuple[bool, Any]]:
        """Fetch leagues from the API and download their emblems.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if leagues were fetched successfully.
                - data (list/dict): List of leagues with emblem image bytes or error messages.
        """
        try:
            data = await self.__api.get("competitions/")

            # Filter only desired leagues
            leagues = [league for league in data["competitions"] if league["code"] in self.__leagues]

            async with aiohttp.ClientSession() as session:
                tasks = []
                for league in leagues:
                    task = asyncio.create_task(self.__fetch_image(session, league['emblem']))
                    tasks.append((league, task))

                competitions = []
                for league, task in tasks:
                    image_bytes = await task
                    competitions.append({
                        "id": league['id'],
                        "name": league['name'],
                        "code": league['code'],
                        "emblem": image_bytes
                    })

            return True, competitions

        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in fetch_leagues:", e)
            return False, [str(e)]

    async def fetch_teams(self, league_code: str) -> Optional[Tuple[bool, Any]]:
        """Fetch teams for a given league and download their emblems.

        Args:
            league_code (str): Code of the league to fetch teams from.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if teams were fetched successfully.
                - data (tuple): List of team dicts with emblems and league name, or error messages.
        """
        try:
            # Fetch team data from API
            data = await self.__api.get(f"competitions/{league_code}/standings")
            table = data["standings"][0]["table"]

            async with aiohttp.ClientSession() as session:
                # Prepare concurrent image fetch tasks
                tasks = []
                for team in table:
                    crest_url = team['team']['crest']
                    task = asyncio.create_task(self.__fetch_image(session, crest_url))
                    tasks.append((team, task))

                # Collect results concurrently
                teams = []
                for team, task in tasks:
                    image_bytes = await task
                    teams.append({
                        "id": team['team']['id'],
                        "name": team['team']['shortName'],
                        "emblem": image_bytes
                    })

            return True, (teams, data['competition']['name'])
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in fetch_teams:", e)
            return False, [str(e)]

    async def fetch_matches(self, team_code: int) -> Optional[Tuple[bool, Any]]:
        """Fetch upcoming matches for a team, including team emblems.

        Args:
            team_code (int): ID of the team to fetch matches for.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if matches were fetched successfully.
                - data (list): List of match dictionaries with team info, dates, competition, or error messages.
        """
        try:
            current_date = date.today()
            six_months_after = current_date + relativedelta(months=6)

            current_date_str = current_date.strftime("%Y-%m-%d")
            six_months_after_str = six_months_after.strftime("%Y-%m-%d")

            # Fetch match data
            data = await self.__api.get(
                f"teams/{team_code}/matches?dateFrom={current_date_str}&dateTo={six_months_after_str}&limit=50"
            )

            matches_data = data["matches"]

            async with aiohttp.ClientSession() as session:
                tasks = []

                for match in matches_data:
                    home_url = match['homeTeam']['crest']
                    away_url = match['awayTeam']['crest']

                    home_task = asyncio.create_task(self.__fetch_image(session, home_url))
                    away_task = asyncio.create_task(self.__fetch_image(session, away_url))
                    tasks.append((match, home_task, away_task))

                results = []
                for match, home_task, away_task in tasks:
                    home_img, away_img = await asyncio.gather(home_task, away_task)
                    results.append({
                        "id": match['id'],
                        "home_name": match['homeTeam']['shortName'],
                        "home_emblem": home_img,
                        "away_name": match['awayTeam']['shortName'],
                        "away_emblem": away_img,
                        "date": match['utcDate'],
                        "competition": match['competition']['name'],
                        "home_id": match['homeTeam']['id'],
                        "away_id": match['awayTeam']['id']
                    })

            return True, results[:20]
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in fetch_matches:", e)
            return False, [str(e)]

    async def fetch_h2h(self, match_code: int) -> Optional[Tuple[bool, Any]]:
        """Fetch head-to-head history for a specific match.

        Args:
            match_code (int): Match ID to fetch head-to-head data for.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if H2H data was fetched successfully.
                - data (list): List of previous matches and ML models dictionary, or error messages.
        """
        try:

            # Fetch match data
            data = await self.__api.get(
                f"matches/{match_code}/head2head?limit=50"
            )

            matches_data = data["matches"]

            match_list = []
            for match in matches_data:
                value = {
                    "competition": match['competition']['name'],
                    "date": match['utcDate'],
                    "homeTeam": match['homeTeam']['shortName'],
                    "awayTeam": match['awayTeam']['shortName'],
                    "homeScore": match['score']['fullTime']['home'],
                    "awayScore": match['score']['fullTime']['away']
                }
                match_list.append(value)

            return True, [match_list, self.__ml_models]
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in fetch_matches:", e)
            return False, [str(e)]

    async def predict_scores(self, home_id: int, away_id: int, match_id: int, code: list) -> Optional[Tuple[bool, Any]]:
        """Predict match scores and probabilities using ML models.

        Args:
            home_id (int): Home team ID.
            away_id (int): Away team ID.
            match_id (int): Match ID.
            code (list): Binary list indicating which ML models to use for prediction.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if prediction was successful.
                - data (dict): Predicted scores and probabilities, or error messages.
        """
        try:
            match_data = await self.__api.get(f"matches/{match_id}")

            home_name = match_data['homeTeam']['shortName']
            away_name = match_data['awayTeam']['shortName']

            home_elo = await self.__storage.get_elo(home_name)
            away_elo = await self.__storage.get_elo(away_name)

            current_date = date.today()
            one_day_before = current_date - relativedelta(days=1)
            six_months_before = current_date - relativedelta(months=6)

            one_day_before_str = one_day_before.strftime("%Y-%m-%d")
            six_months_before_str = six_months_before.strftime("%Y-%m-%d")

            home_team_data = await self.__api.get(
                f"teams/{home_id}/matches?dateFrom={six_months_before_str}&dateTo={one_day_before_str}&limit=5")

            away_team_data = await self.__api.get(
                f"teams/{away_id}/matches?dateFrom={six_months_before_str}&dateTo={one_day_before_str}&limit=5")

            home_stats = self.__calculate_last5_stats(home_id, home_team_data)
            away_stats = self.__calculate_last5_stats(away_id, away_team_data)

            features = [home_elo, away_elo]
            for value in home_stats.values():
                features.append(value)

            for value in away_stats.values():
                features.append(value)

            predictions = await self.__make_prediction(code, features)

            code_str = ""
            for value in code:
                code_str += str(value)

            await self.__storage.insert_prediction(
                match_id, code_str, home_id, predictions['Expected_Home_Goals'],
                away_id, predictions['Expected_Away_Goals'],
                predictions['P_HomeWin'], predictions['P_Draw'], predictions['P_AwayWin'],
                home_name, away_name
            )

            return True, predictions
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in predict_scores:", e)
            return False, [str(e)]

    async def cleanup(self) -> None:
        """Close the storage connection and clean up resources."""
        await self.__storage.close_connection()

    @staticmethod
    async def __fetch_image(session, url: str) -> Optional[dict]:
        """Download image bytes from a URL using an aiohttp session.

        Args:
            session (aiohttp.ClientSession): The aiohttp session to use.
            url (str): URL of the image to fetch.

        Returns:
            bytes: The image data in bytes, or None if fetch fails.
        """
        async with session.get(url) as response:
            return await response.read()

    @staticmethod
    def __match_probabilities(l_home: float, l_away: float, max_goals: int = 10) -> Optional[np.array]:
        """Calculate match score probabilities using a Poisson distribution.

        Args:
            l_home (float): Expected goals for home team.
            l_away (float): Expected goals for away team.
            max_goals (int): Maximum goals considered for probability matrix.

        Returns:
            np.array: Matrix of probabilities for all possible score combinations.
        """
        probs = np.zeros((max_goals + 1, max_goals + 1))
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                probs[i, j] = poisson.pmf(i, l_home) * poisson.pmf(j, l_away)
        return probs

    @staticmethod
    def __calculate_last5_stats(team_id: int, team_data: dict) -> dict:
        """Calculate last 5 match statistics for a team.

        Args:
            team_id (int): Team ID.
            team_data (dict): Match data containing the last 5 matches.

        Returns:
            dict: Aggregated stats including points, goals, wins, draws, losses.
        """
        points, wins, draws, losses = 0, 0, 0, 0
        goals_for, goals_against = 0, 0

        for match in team_data['matches']:
            if match['status'] != "FINISHED":
                continue

            is_home = match['homeTeam']['id'] == team_id
            gf = match['score']['fullTime']['home'] if is_home else match['score']['fullTime']['away']
            ga = match['score']['fullTime']['away'] if is_home else match['score']['fullTime']['home']

            goals_for += gf
            goals_against += ga

            if gf > ga:
                wins += 1
                points += 3
            elif gf == ga:
                draws += 1
                points += 1
            else:
                losses += 1

        return {
            "points": points,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "wins": wins,
            "draws": draws,
            "losses": losses,
        }

    async def __make_prediction(self, code: list, features: list) -> dict:
        """Predict expected goals and match outcome probabilities using ML models.

        Args:
            code (list): Binary list indicating which ML models to use.
            features (list): Feature vector for prediction.

        Returns:
            dict: Dictionary containing expected goals and probabilities for home win, draw, and away win.
        """
        warnings.filterwarnings("ignore", message="X does not have valid feature names")

        def _run_prediction():
            features_arr = np.array([features])

            scaler = joblib.load(resource_path("./Assets/models/scaler.pkl"))
            features_scaled = scaler.transform(features_arr)

            home_xg = []
            away_xg = []

            for i, (key, (paths, _)) in enumerate(self.__ml_models.items()):
                if code[i]:
                    home_model = joblib.load(resource_path(paths[0]))
                    home_result = home_model.predict(features_scaled)
                    home_xg.append(home_result.item())

                    away_model = joblib.load(resource_path(paths[1]))
                    away_result = away_model.predict(features_scaled)
                    away_xg.append(away_result.item())

            return home_xg, away_xg

        # Run the blocking work in a separate thread
        home_xg, away_xg = await asyncio.to_thread(_run_prediction)

        home_xg = np.array(home_xg).mean().item()
        away_xg = np.array(away_xg).mean().item()

        probs = self.__match_probabilities(home_xg, away_xg)
        p_home_win = np.tril(probs, -1).sum()
        p_away_win = np.triu(probs, 1).sum()
        p_draw = np.trace(probs)

        result = {
            'Expected_Home_Goals': home_xg,
            'Expected_Away_Goals': away_xg,
            'P_HomeWin': p_home_win,
            'P_Draw': p_draw,
            'P_AwayWin': p_away_win,
        }

        return result
