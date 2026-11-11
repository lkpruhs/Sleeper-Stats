import requests

class SleeperClient:
    BASE_URL = "https://api.sleeper.app/v1"

    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint):
        """Helper method to handle GET requests and error checking."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            return None

    def get_league_info(self, league_id):
        """Fetch basic settings and info for a specific league."""
        return self._get(f"league/{league_id}")

    def get_rosters(self, league_id):
        """Fetch all rosters in the league."""
        return self._get(f"league/{league_id}/rosters")

    def get_users(self, league_id):
        """Fetch all users/managers in the league."""
        return self._get(f"league/{league_id}/users")

    def get_matchups(self, league_id, week):
        """Fetch matchups for a specific week."""
        return self._get(f"league/{league_id}/matchups/{week}")

def main():
    # Start with the provided league ID and iterate backward
    league_id = "1311996156489773056"
    client = SleeperClient()

    print("Querying Sleeper API for historical 2nd-lowest scoring victories...\n")

    while league_id:
        league_info = client.get_league_info(league_id)
        if not league_info:
            break
            
        season = league_info.get("season")
        
        users = client.get_users(league_id)
        rosters = client.get_rosters(league_id)
        
        if not users or not rosters:
            league_id = league_info.get("previous_league_id")
            continue

        # Map owner IDs to display names for clean output
        user_map = {u["user_id"]: u.get("display_name", "Unknown") for u in users}
        roster_map = {r["roster_id"]: user_map.get(r["owner_id"], f"Team {r['roster_id']}") for r in rosters}
        
        # Sleeper regular seasons and playoffs typically run through week 18
        for week in range(1, 19):
            matchups = client.get_matchups(league_id, week)
            if not matchups:
                continue
                
            # Skip unplayed future/current weeks (where all scores are 0)
            if all(m.get("points", 0) == 0 for m in matchups):
                continue
                
            # Group matchups by matchup_id to verify head-to-head games
            games = {}
            for m in matchups:
                mid = m.get("matchup_id")
                if mid is None:
                    continue
                if mid not in games:
                    games[mid] = []
                games[mid].append({
                    "roster_id": m["roster_id"],
                    "points": m.get("points", 0)
                })
                
            playing_teams = []
            for mid, teams in games.items():
                if len(teams) == 2:
                    playing_teams.extend(teams)
                    
            if len(playing_teams) < 2:
                continue
                
            # Sort all teams playing this week by points to isolate the 2nd lowest
            sorted_teams = sorted(playing_teams, key=lambda x: x["points"])
            second_lowest = sorted_teams[1]
            
            # Find the opponent of the 2nd lowest scoring team
            for mid, teams in games.items():
                if len(teams) == 2:
                    if teams[0]["roster_id"] == second_lowest["roster_id"]:
                        my_team, opponent = teams[0], teams[1]
                        break
                    elif teams[1]["roster_id"] == second_lowest["roster_id"]:
                        my_team, opponent = teams[1], teams[0]
                        break
            else:
                continue
                
            # If the 2nd lowest scorer outscored their direct opponent, they won the matchup
            if my_team["points"] > opponent["points"]:
                winner_name = roster_map.get(my_team["roster_id"], "Unknown")
                loser_name = roster_map.get(opponent["roster_id"], "Unknown")
                print(f"Year: {season} | Week: {week} | Matchup: {winner_name} ({my_team['points']}) def. {loser_name} ({opponent['points']})")
                
        # Traverse backward to the previous year's league ID
        league_id = league_info.get("previous_league_id")

if __name__ == "__main__":
    main()


