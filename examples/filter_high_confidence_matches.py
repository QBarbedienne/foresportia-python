from foresportia import ForesportiaClient


CONFIDENCE_THRESHOLD = 0.7
HIGH_LABELS = {"high", "very high", "strong", "stable"}


def field(match: dict, *names: str) -> object:
    for name in names:
        value = match.get(name)
        if value not in (None, ""):
            return value
    return None


def is_high_signal(value: object) -> bool:
    if isinstance(value, (int, float)):
        return float(value) >= CONFIDENCE_THRESHOLD

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in HIGH_LABELS:
            return True
        try:
            numeric_value = float(normalized.rstrip("%"))
        except ValueError:
            return False
        if normalized.endswith("%"):
            return numeric_value >= CONFIDENCE_THRESHOLD * 100
        return numeric_value >= CONFIDENCE_THRESHOLD

    return False


with ForesportiaClient.from_env() as client:
    data = client.picks_today()

matches = data.get("matches", [])
filtered_matches = []

for match in matches:
    confidence = field(match, "confidence", "confidence_score", "confidence_label")
    stability = field(match, "stability", "stability_score", "stability_label")
    if is_high_signal(confidence) or is_high_signal(stability):
        filtered_matches.append(match)

print(f"High-confidence matches: {len(filtered_matches)}")

for match in filtered_matches:
    home_team = field(match, "home_team") or "Home"
    away_team = field(match, "away_team") or "Away"
    pick = field(match, "pick", "predicted_pick", "prediction") or "n/a"
    confidence = field(match, "confidence", "confidence_score", "confidence_label") or "n/a"
    stability = field(match, "stability", "stability_score", "stability_label") or "n/a"

    print(
        f"{home_team} vs {away_team} | "
        f"pick: {pick} | confidence: {confidence} | stability: {stability}"
    )
