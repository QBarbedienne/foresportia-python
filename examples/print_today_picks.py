from foresportia import ForesportiaClient


def display_value(value: object, fallback: str = "n/a") -> object:
    return fallback if value in (None, "") else value


with ForesportiaClient.from_env() as client:
    data = client.picks_today()

matches = data.get("matches", [])
print(f"Today's picks: {len(matches)}")

for match in matches:
    home_team = display_value(match.get("home_team"), "Home")
    away_team = display_value(match.get("away_team"), "Away")
    pick = display_value(match.get("pick") or match.get("predicted_pick"))
    confidence = display_value(
        match.get("confidence") or match.get("confidence_label") or match.get("stability")
    )
    likely_score = display_value(match.get("likely_score") or match.get("predicted_score"))

    print(
        f"{home_team} vs {away_team} | "
        f"pick: {pick} | confidence: {confidence} | likely score: {likely_score}"
    )
