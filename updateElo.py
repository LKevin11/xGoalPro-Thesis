import sqlite3
import pandas as pd
from soccerdata import ClubElo
import os

# ================= CONFIG =================
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xGoalPro/Assets/predictions.db")
TABLE_NAME = "eloScores"
DATE = None  # None = latest ELO snapshot

# ================= MAIN =================

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Load team names from DB
elo_names = pd.read_sql_query(f"SELECT eloName FROM {TABLE_NAME}", conn)

# Load latest ClubElo snapshot
elo = ClubElo()
df_elo = elo.read_by_date(DATE)  # index = team name
df_elo.index = df_elo.index.str.strip()  # clean whitespace

updated, missing = 0, []

# Loop over each team in DB
for _, row in elo_names.iterrows():
    team_name = row["eloName"]
    team_lower = team_name.lower().strip()

    # Try exact match (case-insensitive)
    matched = df_elo.loc[df_elo.index.str.lower() == team_lower]

    if matched.empty:
        # Try partial match
        mask = df_elo.index.str.contains(team_name, case=False, regex=False)
        matched = df_elo.loc[mask]

    if not matched.empty:
        latest_elo = float(matched.iloc[0]["elo"])
        cur.execute(
            f"UPDATE {TABLE_NAME} SET elo = ? WHERE eloName = ?",
            (latest_elo, team_name),
        )
        updated += 1
        print(f"✅ Updated {team_name} → {latest_elo}")
    else:
        missing.append(team_name)
        print(f"⚠️ No match found for {team_name}")

# Commit and close
conn.commit()
conn.close()

print(f"\n✅ Done. Updated {updated} teams.")
if missing:
    print("⚠️ No ELO found for:", ", ".join(missing))
