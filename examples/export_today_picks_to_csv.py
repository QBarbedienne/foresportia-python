import csv

from foresportia import ForesportiaClient


OUTPUT_FILE = "today_picks.csv"


def field(match: dict, *names: str) -> object:
    for name in names:
        value = match.get(name)
        if value not in (None, ""):
            return value
    return ""


with ForesportiaClient.from_env() as client:
    data = client.picks_today()

matches = data.get("matches", [])

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(
        csv_file,
        fieldnames=[
            "match_id",
            "league",
            "date",
            "home_team",
            "away_team",
            "pick",
            "home_probability",
            "draw_probability",
            "away_probability",
            "confidence",
            "stability",
            "likely_score",
        ],
    )
    writer.writeheader()

    for match in matches:
        writer.writerow(
            {
                "match_id": field(match, "id", "match_id"),
                "league": field(match, "league", "league_code", "competition"),
                "date": field(match, "date", "kickoff", "kickoff_at"),
                "home_team": field(match, "home_team"),
                "away_team": field(match, "away_team"),
                "pick": field(match, "pick", "predicted_pick", "prediction"),
                "home_probability": field(
                    match, "home_probability", "home_win_probability"
                ),
                "draw_probability": field(match, "draw_probability"),
                "away_probability": field(
                    match, "away_probability", "away_win_probability"
                ),
                "confidence": field(
                    match, "confidence", "confidence_label", "confidence_score"
                ),
                "stability": field(
                    match, "stability", "stability_label", "stability_score"
                ),
                "likely_score": field(
                    match, "likely_score", "likely_scores", "predicted_score", "scoreline"
                ),
            }
        )

print(f"Wrote {len(matches)} matches to {OUTPUT_FILE}")
