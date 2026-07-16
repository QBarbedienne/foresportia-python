# Plans and Limitations

Developer and Starter are active public API plans. They use the same `/v1`
endpoints, `X-API-Key` authentication, match IDs, SDK models, pagination, and
error handling. Upgrading to Starter does not require rewriting an integration.

| Capability | Developer — free | Starter — paid |
|---|---:|---:|
| Competitions | 1 | 20 |
| Verified history | up to 7 days | up to 90 days |
| Match IDs per bulk request | up to 5 | up to 100 |
| Analytics | limited projection | more complete analytics |

The server contract is the source of truth for the exact entitlement attached
to a key. The SDK deliberately does not infer a plan from the key prefix.

## History

`list_league_matches()` accepts a maximum date-window size of 31 days per
request. This request limit is distinct from plan history:

- Developer can access up to 7 days of verified history.
- Starter can access up to 90 days of verified history.
- `history_available_from` may make the currently populated archive shallower.
- The historical archive fills progressively.
- `history_window_exceeded` is a normal business error when a request falls
  outside the effective entitlement.

Use cursor pagination when the selected window contains more rows than one
page. Pagination does not extend the plan's historical entitlement.

## Availability and analytics

Developer returns a useful but limited analytics projection. The
`availability` map explains selected omissions without turning them into SDK
errors. For example:

```python
detail = client.get_match(match_id).data
if detail.availability:
    elo_status = detail.availability.get("ratings.elo_home")
    if elo_status == "starter_required":
        print("Home ELO is reserved for Starter")
```

Values and paths may evolve, so treat this map as tolerant data. Common values
include `starter_required`, `not_available`, and future detailed objects. List
responses expose only their own summary payload; they do not promise every
analytics field available on match detail.

## Bulk

`BULK_MAX_MATCH_IDS = 100` is the SDK's API-wide technical ceiling. Developer
requests with 6–100 IDs are sent normally and the server returns
`bulk_limit_exceeded`. This preserves the server as the authority and keeps the
same SDK code usable after upgrading to Starter.

## Legacy beta

Legacy beta keys remain temporarily compatible. They may have different
competition, endpoint, or data-window entitlements. New integrations should
start with Developer or Starter.

## General limitations

- Coverage and refresh timing vary by competition and currently published data.
- Optional model fields may be absent or `null`; tolerant models retain the full
  payload in `.raw`.
- Retries are disabled by default because a timed-out request may already have
  consumed quota.
- The SDK is synchronous and has no built-in disk cache.
- Foresportia provides probabilities and analytics, not bookmaker odds,
  guaranteed outcomes, or betting advice.
