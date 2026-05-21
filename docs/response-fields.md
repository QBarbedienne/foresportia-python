# Response Fields

The Foresportia API is currently in private beta. Response schemas may evolve as
endpoints mature, coverage expands, and model metadata is refined.

The SDK returns API responses as dictionaries. Application code should use
`.get()` for fields that may be optional, missing, renamed, or unavailable for a
specific match.

## Top-Level Shape

Match-list endpoints commonly return a dictionary with a `matches` list:

```python
data = client.picks_today()
matches = data.get("matches", [])
```

Other metadata may be present depending on the endpoint, such as pagination,
usage information, plan information, or request context.

## Match Identifiers, Teams, League, and Date

Match objects may include fields such as:

- `id`, `match_id`, or another match identifier.
- `home_team` and `away_team`.
- `league`, `league_code`, `competition`, or related league metadata.
- `date`, `kickoff`, `kickoff_at`, or another date/time field.
- `status` for scheduled, live, postponed, finished, or similar match states.

Field names and availability may differ by endpoint during beta. If your code
needs a stable internal identifier, store the value defensively and be prepared
to handle missing IDs.

## Probabilities

Probability fields may be represented as separate fields or grouped objects,
depending on the endpoint and beta schema version. Common possibilities include:

- `home_probability`
- `draw_probability`
- `away_probability`
- `probabilities`
- `home_win_probability`
- `away_win_probability`

Probabilities are model outputs, not guarantees. They may be expressed as
fractions, percentages, or structured values depending on the endpoint. Check the
actual response returned to your beta account before formatting or comparing
values.

## Predicted Pick

A predicted pick may be present as:

- `pick`
- `predicted_pick`
- `prediction`
- another endpoint-specific field

Treat the pick as the model-preferred outcome for the match data returned by the
API. It is not betting advice and should not be presented as a guaranteed
result.

## Confidence and Stability Indicators

Some responses may include confidence, stability, or quality indicators. These
fields may appear as:

- `confidence`
- `confidence_label`
- `confidence_score`
- `stability`
- `stability_label`
- `stability_score`

These indicators are intended to help interpret model output cautiously. They do
not guarantee accuracy and should not be converted into performance claims
without independent validation.

## Likely Scores

Likely score information may be available for some matches and absent for
others. Possible fields include:

- `likely_score`
- `likely_scores`
- `predicted_score`
- `scoreline`

Likely scores should be treated as model analytics, not final-score forecasts or
guaranteed outcomes.

## Optional Fields and Missing Values

During beta, a field may be missing because:

- The endpoint does not currently include it.
- The match is outside available coverage.
- The model output is not available yet.
- The match status changed.
- The beta schema changed.

Use `.get()` and sensible fallbacks:

```python
pick = match.get("pick") or match.get("predicted_pick") or "n/a"
confidence = match.get("confidence") or match.get("confidence_label") or "n/a"
```

Avoid assuming that every match has probabilities, confidence labels, likely
scores, or identical field names across endpoints until the stable API schema is
published.
