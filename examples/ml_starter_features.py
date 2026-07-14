"""Build a simple feature matrix from Foresportia matches for ML experiments.

This example fetches upcoming matches for one competition, extracts the model
probabilities and a few context fields into a feature matrix, and (optionally)
fits a small scikit-learn model on past labeled rows you may already have.

Requirements:
    pip install foresportia
    pip install "foresportia[ml]"   # optional: numpy + scikit-learn

Set your API key first:
    export FORES_API_KEY="fs_beta_your_key_here"

Foresportia provides model probabilities and analytics only. Nothing here is
a guaranteed prediction, and this script is not betting advice.
"""

from __future__ import annotations

from foresportia import ForesportiaClient, MatchSummary

LEAGUE_CODE = "PREMIER_LEAGUE"  # any competition enabled for your key


def match_features(match: MatchSummary) -> dict[str, float | None]:
    """Extract a flat feature dict from one match summary."""

    probabilities = match.probabilities or {}
    markets = match.markets or {}
    confidence = match.confidence or {}
    return {
        "p_home": probabilities.get("home"),
        "p_draw": probabilities.get("draw"),
        "p_away": probabilities.get("away"),
        "btts": markets.get("btts"),
        "over_2_5": markets.get("over_2_5"),
        "dnb_home": markets.get("dnb_home"),
        "confidence": confidence.get("score"),
    }


def main() -> None:
    with ForesportiaClient.from_env() as client:
        response = client.list_league_matches(LEAGUE_CODE, include="upcoming", days=14)

    rows = []
    for match in response.data or []:
        features = match_features(match)
        if features["p_home"] is None:
            continue  # skip matches without published probabilities
        rows.append((match.id, f"{match.home_team} vs {match.away_team}", features))

    print(f"Collected {len(rows)} upcoming matches with features.")
    for match_id, label, features in rows[:5]:
        print(f"  {label}: {features}")

    # Optional: turn the features into a matrix and fit a tiny model.
    # You need your own historical labels (e.g. final outcomes) to train
    # anything meaningful; the snippet below only shows the mechanics.
    try:
        import numpy as np
        from sklearn.linear_model import LogisticRegression
    except ImportError:
        print("\nInstall the optional extra for the ML part: pip install 'foresportia[ml]'")
        return

    feature_names = ["p_home", "p_draw", "p_away", "btts", "over_2_5", "confidence"]
    matrix = np.array(
        [[features.get(name) or 0.0 for name in feature_names] for _, _, features in rows],
        dtype=float,
    )
    print(f"\nFeature matrix shape: {matrix.shape}")

    # Placeholder labels: replace with real historical outcomes before training.
    if len(matrix) >= 4:
        fake_labels = (matrix[:, 0] > matrix[:, 2]).astype(int)
        model = LogisticRegression().fit(matrix, fake_labels)
        print("Fitted a demo LogisticRegression (replace labels with real outcomes).")
        print("Coefficients:", dict(zip(feature_names, model.coef_[0].round(3))))


if __name__ == "__main__":
    main()
