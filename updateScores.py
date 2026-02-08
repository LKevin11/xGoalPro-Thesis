import sqlite3
import requests
import json
import time
import os

# --- CONFIG ---
API_KEY = "0ae181e65f9a4cc2aff8cc7ea67ff169"
API_URL_TEMPLATE = "http://api.football-data.org/v4/matches/"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xGoalPro/Assets/predictions.db")

HEADERS = {"X-Auth-Token": API_KEY}


def fetch_match_data(match_id):
    """Fetch match data from API"""
    url = API_URL_TEMPLATE + str(match_id)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        try:
            home_score = data["score"]["fullTime"]["home"]
            away_score = data["score"]["fullTime"]["away"]
            return home_score, away_score
        except KeyError:
            print(f"⚠️ Missing score data for match {match_id}")
            return None, None
    else:
        print(f"❌ Error fetching {match_id}: {response.status_code} - {response.text}")
        return None, None


def update_scores_in_db():
    """Fetch all match IDs and update their scores"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch all match IDs
    cur.execute("SELECT match_id FROM predictions WHERE real_home_score = -1 AND real_away_score = -1")
    matches = cur.fetchall()

    print(f"Found {len(matches)} matches to update...")

    for (match_id,) in matches:
        home, away = fetch_match_data(match_id)
        if home is not None and away is not None:
            cur.execute(
                """
                UPDATE predictions
                SET real_home_score = ?, real_away_score = ?
                WHERE match_id = ? AND real_home_score = -1 AND real_away_score = -1
                """,
                (home, away, match_id),
            )
            conn.commit()
            print(f"✅ Updated match {match_id}: {home}-{away}")

        # To avoid hitting API rate limits
        time.sleep(1.2)

    conn.close()
    print("🏁 All matches updated successfully.")


if __name__ == "__main__":
    update_scores_in_db()
