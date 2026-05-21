from foresportia import ForesportiaClient


client = ForesportiaClient.from_env()
data = client.world_cup_2026_matches(limit=10)
matches = data.get("matches", [])
print(f"World Cup 2026 matches: {len(matches)}")
for match in matches[:3]:
    print(match.get("home_team"), "vs", match.get("away_team"), "-", match.get("pick"))
