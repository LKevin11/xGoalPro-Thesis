import asyncio
import aiohttp

from Persistence.DataLoader import IDataLoader
from Persistence.StorageInterface import IPredictionStorage
from Persistence.Api import IApi
from typing import Optional, Tuple, Any

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class StatisticsModel:
    """Model for fetching and managing football statistics and predictions.

    This model interacts with a league API, a data loader, and a prediction storage
    interface to fetch league-, team-, and prediction data. It also
    supports downloading league emblems as image bytes.

    Attributes:
        __league_api (IApi): API interface for fetching league data and emblems.
        __statistic_data_loader (IDataLoader): Data loader for league and team statistics.
        __storage (IPredictionStorage): Storage interface for retrieving prediction data.
        __leagues (dict): Dictionary mapping league codes to human-readable league names.
    """

    def __init__(self, league_api, data_loader, storage):
        """Initialize StatisticsModel with API, data loader, and storage.

        Args:
            league_api (IApi): API interface to fetch league data.
            data_loader (IDataLoader): Interface to fetch league and team statistics.
            storage (IPredictionStorage): Interface to fetch prediction data.
        """
        self.__league_api: IApi = league_api
        self.__statistic_data_loader: IDataLoader = data_loader
        self.__storage: IPredictionStorage = storage
        self.__leagues = {}

    def add_league(self, league_code, league_name) -> None:
        """Add a league code and name to track in the model.

        Args:
            league_code (str): Short code identifying the league (e.g., 'PL').
            league_name (str): Human-readable name for the league.
        """
        self.__leagues[league_code] = league_name

    async def fetch_leagues(self) -> Optional[Tuple[bool, Any]]:
        """Fetch leagues from the API and download their emblems.

        Only leagues that were previously added using `add_league` are fetched.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if leagues were fetched successfully.
                - data (list): List of leagues with ID, code, long name, and emblem bytes,
                  or error messages if the fetch fails.
        """
        try:
            data = await self.__league_api.get("competitions/")

            # Filter only desired leagues by code
            desired_codes = set(self.__leagues.keys())
            leagues = [
                league for league in data["competitions"]
                if league["code"] in desired_codes
            ]

            async with aiohttp.ClientSession() as session:
                tasks = []
                for league in leagues:
                    task = asyncio.create_task(self.__fetch_image(session, league["emblem"]))
                    tasks.append((league, task))

                competitions = []
                for league, task in tasks:
                    image_bytes = await task
                    competitions.append({
                        "id": league["id"],
                        "name": league["name"],
                        "code": league["code"],
                        "long_name": self.__leagues.get(league["code"]),  # the stored name
                        "emblem": image_bytes
                    })

            return True, competitions
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            print("Error in fetch_leagues:", e)
            return False, [str(e)]

    async def fetch_league_statistics(self, league: str) -> Optional[Tuple[bool, Any]]:
        """Fetch league-level statistics, including standings, player stats, and results.

        Args:
            league (str): League code to fetch statistics for.

        Returns:
            Optional[Tuple[bool, Any]]: 
                - success (bool): True if data was fetched successfully.
                - data (list): [table_data, player_data, results_data] or error messages.
        """
        try:

            data = await self.__league_api.get(f"competitions/{league}/standings")
            table = data["standings"][0]["table"]

            async with aiohttp.ClientSession() as session:
                tasks = []
                for team in table:
                    crest_url = team['team']['crest']
                    task = asyncio.create_task(self.__fetch_image(session, crest_url))
                    tasks.append((team, task))

                teams = []
                for team, task in tasks:
                    image_bytes = await task
                    teams.append({
                        "id": team['team']['id'],
                        "name": team['team']['shortName'],
                        "emblem": image_bytes,
                        "playedGames": team['playedGames'],
                        "won": team['won'],
                        "draw": team['draw'],
                        "lost": team['lost'],
                        "points": team['points'],
                        "goalsFor": team['goalsFor'],
                        "goalsAgainst": team['goalsAgainst'],
                        "goalDifference": team['goalDifference']
                    })
            
            data = await self.__league_api.get(f"competitions/{league}/scorers")
            scorers = data["scorers"]

            async with aiohttp.ClientSession() as session:
                tasks = []
                for player in scorers:
                    crest_url = player['team']['crest']
                    task = asyncio.create_task(self.__fetch_image(session, crest_url))
                    tasks.append((player, task))

                players = []
                for player, task in tasks:
                    image_bytes = await task
                    players.append({
                        "id": player['team']['id'],
                        "name": player['team']['shortName'],
                        "emblem": image_bytes,
                        "player_name": player['player']['name'],
                        "playedMatches": player['playedMatches'],
                        "goals": player['goals'],
                        "assists": player['assists'] if player['assists'] is not None else 0
                    })

            current_date = date.today()

            start_date = data['season']['startDate']
            end_date = current_date

            start_date_str = start_date.split('T')[0]
            end_date_str = end_date.strftime("%Y-%m-%d")

            data = await self.__league_api.get(
                f"competitions/{league}/matches?dateFrom={start_date_str}&dateTo={end_date_str}&limit=50"
            )
            matches = data['matches']

            async with aiohttp.ClientSession() as session:
                tasks = []

                for match in matches:
                    home_url = match['homeTeam']['crest']
                    away_url = match['awayTeam']['crest']

                    home_task = asyncio.create_task(self.__fetch_image(session, home_url))
                    away_task = asyncio.create_task(self.__fetch_image(session, away_url))
                    tasks.append((match, home_task, away_task))

                results = []
                for match, home_task, away_task in tasks:
                    home_img, away_img = await asyncio.gather(home_task, away_task)
                    results.append({
                        "home_name": match['homeTeam']['shortName'],
                        "home_emblem": home_img,
                        "score": f"{match['score']['fullTime']['home']} : {match['score']['fullTime']['away']}" ,
                        "away_name": match['awayTeam']['shortName'],
                        "away_emblem": away_img,
                        "date": match['utcDate']
                    })

            return True, [teams, players, results]

        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            return False, [str(e)]

    async def fetch_team_statistics(self, team: int) -> Optional[Tuple[bool, Any]]:
        """Fetch team-level statistics including players, results, and aggregated stats.

        Args:
            team (str): Name or code of the team.

        Returns:
            Optional[Tuple[bool, Any]]:
                - success (bool): True if team data was fetched successfully.
                - data (list): [players_list, team_results, team_stats] or error messages.
        """
        try:
            team_data = await self.__league_api.get(f"teams/{team}")


            today = date.today()

            if today.month >= 8:
                start_date = date(today.year, 8, 1)
            else:
                start_date = date(today.year - 1, 8, 1)

            end_date = today

            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            data = await self.__league_api.get(
                f"teams/{team}/matches?dateFrom={start_date_str}&dateTo={end_date_str}&limit=50"
            )
            matches = data['matches']

            results = []
            for match in matches:
                results.append({
                    "home_name": match['homeTeam']['shortName'],
                    "score": f"{match['score']['fullTime']['home']} : {match['score']['fullTime']['away']}" ,
                    "away_name": match['awayTeam']['shortName'],
                    "date": match['utcDate']
                })

            return True, [team_data, results]
        
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                return False, ["Too many requests – you can make up to 10 API calls per minute."]

        except Exception as e:
            return False, [str(e)]

    async def fetch_predictions(self) -> Optional[Tuple[bool, Any]]:
        """Fetch all stored match predictions from storage.

        Returns:
            Optional[Tuple[bool, Any]]:
                - success (bool): True if predictions were fetched successfully.
                - data (list): List of prediction records or error messages.
        """
        try:

            data = await self.__storage.get_all_predictions()
            return True, data

        except Exception as e:
            return False, [str(e)]

    async def cleanup(self) -> None:
        """Close the storage connection and clean up resources."""
        await self.__storage.close_connection()

    @staticmethod
    async def __fetch_image(session, url) -> Optional[dict]:
        """Download an image from a URL using an aiohttp session.

        Args:
            session (aiohttp.ClientSession): Active HTTP session to perform the request.
            url (str): URL of the image to fetch.

        Returns:
            bytes: Image data as bytes, or None if fetching fails.
        """
        async with session.get(url) as response:
            return await response.read()
