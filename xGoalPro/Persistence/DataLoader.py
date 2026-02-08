import aiohttp

from understat import Understat
import pandas as pd


class IDataLoader:
    """Interface for loading football league and team data."""

    async def get_league_table(self, league: str) -> pd.DataFrame:
        """Returns the league table for the given league."""
        ...

    async def get_league_players(self, league: str) -> pd.DataFrame:
        """Returns all players in the given league."""
        ...

    async def get_league_results(self, league: str) -> pd.DataFrame:
        """Returns match results for the given league."""
        ...

    async def get_team_players(self, team: str) -> pd.DataFrame:
        """Returns all players for the given team."""
        ...

    async def get_team_results(self, team: str) -> pd.DataFrame:
        """Returns match results for the given team."""
        ...

    async def get_team_stats(self, team: str) -> dict:
        """Returns statistical data for the given team."""
        ...


class StatisticsDataLoader(IDataLoader):
    """Loads football data using the Understat API for a specific season."""

    def __init__(self, year: str):
        """
        Initializes the data loader for a specific season.

        Args:
            year: The season year, e.g., "2022".
        """
        self.__year: str = year

    async def get_league_table(self, league: str) -> pd.DataFrame:
        """Returns the league table for the given league as a DataFrame."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            table = await understat.get_league_table(league, self.__year)
            table = pd.DataFrame(table)
            table = table[[0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 17]]
            table = table.iloc[1:].reset_index(drop=True)
            return table

    async def get_league_players(self, league: str) -> pd.DataFrame:
        """Returns all players in the given league as a DataFrame."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            table = await understat.get_league_players(league, self.__year)
            table = pd.DataFrame(table)
            table = table[
                ["player_name", "games", "time", "goals",
                 "xG", "assists", "xA", "shots", "key_passes",
                 "yellow_cards", "red_cards", "team_title"]]
            return table

    async def get_league_results(self, league: str) -> pd.DataFrame:
        """Returns match results for the given league as a DataFrame."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            table = await understat.get_league_results(league, self.__year)
            table = pd.DataFrame(table)
            table = table[["h", "a", "goals", "datetime"]]
            return table

    async def get_team_players(self, team: str) -> pd.DataFrame:
        """Returns all players for the given team as a DataFrame."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            table = await understat.get_team_players(team, self.__year)
            table = pd.DataFrame(table)
            table = table[["player_name", "games", "time", "goals",
                           "xG", "assists", "xA", "key_passes",
                           "yellow_cards", "red_cards", "position"]]
            return table

    async def get_team_results(self, team: str) -> pd.DataFrame:
        """Returns match results for the given team as a DataFrame."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            table = await understat.get_team_results(team, self.__year)
            table = pd.DataFrame(table)
            table = table[["h", "a", "goals", "datetime"]]
            return table

    async def get_team_stats(self, team: str) -> dict:
        """Returns statistical data for the given team as a dictionary."""
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)
            stat_dict = await understat.get_team_stats(team, self.__year)
            return stat_dict
