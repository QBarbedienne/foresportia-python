# Foresportia Python SDK

Python SDK for the Foresportia API, a private beta football analytics API that
provides match data, model probabilities, predicted picks, and confidence
signals.

Foresportia returns probabilistic forecasts and analytics. It does not provide
betting advice, bookmaker odds, or guaranteed outcomes, and it is not a live
score feed.

!!! warning "Private beta"
    The SDK and the Foresportia API are currently in private beta. Endpoints,
    response fields, limits, and model outputs may change before a stable
    release.

## Official links

- [Foresportia website](https://www.foresportia.com/en) ([FR](https://www.foresportia.com/) version, [ES](https://www.foresportia.com/es) version)
- [Foresportia API overview](https://www.foresportia.com/en/developers.html)
- [API dashboard](https://www.foresportia.com/en/api-dashboard.html)
- [PyPI package](https://pypi.org/project/foresportia/)
- [GitHub repository](https://github.com/QBarbedienne/foresportia-python)

## Quick install

```bash
pip install foresportia
```

## Quick start

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    account = client.me()
    picks = client.picks_today()

print(account.get("plan"))
print(f"Matches returned: {len(picks.get('matches', []))}")
```

## Documentation

- [Getting Started](getting-started.md) — install, configure your key, and make
  a first request.
- [Authentication](authentication.md) — how API keys are handled.
- [Examples](examples.md) — runnable scripts.
- [Response Fields](response-fields.md) — what API responses may contain.
- [Beta Limitations](beta-limitations.md) — current beta constraints.
