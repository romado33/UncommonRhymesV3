# NHLTopScorers.py

import requests
import pandas as pd

BASE_URL = "https://statsapi.web.nhl.com/api/v1/stats"


# ---------------------------------------------------------
# Fetch skater stats for a given season
# ---------------------------------------------------------
def fetch_skater_season(season):
    url = f"{BASE_URL}?stats=skaterSummary&season={season}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            print(f"⚠️ No skater data for season {season}")
            return None

        rows = []
        for s in splits:
            player = s.get("player", {})
            team = s.get("team", {})
            stat = s.get("stat", {})

            rows.append({
                "seasonId": season,
                "playerId": player.get("id"),
                "skaterFullName": player.get("fullName"),
                "teamAbbrev": team.get("abbreviation"),
                "gamesPlayed": stat.get("games"),
                "goals": stat.get("goals"),
                "assists": stat.get("assists"),
                "points": stat.get("points"),
                "plusMinus": stat.get("plusMinus"),
                "shots": stat.get("shots"),
                "timeOnIcePerGame": stat.get("timeOnIcePerGame"),
                "powerPlayPoints": stat.get("powerPlayPoints"),
                "powerPlayGoals": stat.get("powerPlayGoals"),
                "shortHandedPoints": stat.get("shortHandedPoints"),
                "shortHandedGoals": stat.get("shortHandedGoals"),
                "gameWinningGoals": stat.get("gameWinningGoals"),
            })

        df = pd.DataFrame(rows)
        print(f"✅ Skater data fetched for {season}: {len(df)} players")
        return df

    except requests.exceptions.RequestException as e:
        print(f"❌ Fetch failed for season {season}: {e}")
        return None


# ---------------------------------------------------------
# Fetch team mapping
# ---------------------------------------------------------
def fetch_team_mapping():
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        teams = []
        for t in data.get("teams", []):
            teams.append({
                "teamId": t.get("id"),
                "teamAbbrev": t.get("abbreviation"),
                "teamFullName": t.get("name"),
            })

        df = pd.DataFrame(teams)
        print(f"✅ Team mapping fetched: {len(df)} teams")
        return df
    except requests.exceptions.RequestException as e:
        print(f"❌ Team mapping fetch failed: {e}")
        return pd.DataFrame(columns=["teamId", "teamAbbrev", "teamFullName"])


# ---------------------------------------------------------
# Build dataset across all seasons
# ---------------------------------------------------------
def build_dataset():
    seasons = [
        "20172018", "20182019", "20192020", "20202021",
        "20212022", "20222023", "20232024"
    ]

    frames = []
    for sid in seasons:
        df = fetch_skater_season(sid)
        if df is not None and not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("❌ No skater data could be fetched. Check API.")

    sk = pd.concat(frames, ignore_index=True)

    # Fetch team mapping
    team_map = fetch_team_mapping()
    sk = sk.merge(team_map, on="teamAbbrev", how="left")

    # Rank players within each season by points
    sk["rank_pts"] = sk.groupby("seasonId")["points"].rank(ascending=False, method="first")

    return sk


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
if __name__ == "__main__":
    try:
        data = build_dataset()
        print("✅ Final dataset shape:", data.shape)
        print(data.head(20))

        # Save to CSV
        data.to_csv("nhl_top_scorers.csv", index=False)
        print("📁 Saved dataset to nhl_top_scorers.csv")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
