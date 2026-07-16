"""Developer plan quickstart: future, history, pagination, and availability."""

from foresportia import (
    ForesportiaAPIError,
    ForesportiaClient,
    ForesportiaRateLimitError,
)


COMPETITION = "CHN"  # Replace with the code selected for your Developer plan.


def main() -> None:
    try:
        with ForesportiaClient.from_env() as client:
            future = client.list_league_matches(
                COMPETITION, include="upcoming", days=7, limit=50
            )
            print(f"Future matches: {len(future.data or [])}")

            for match in client.iter_league_matches(
                COMPETITION,
                include="past",
                days=7,
                limit=50,
                max_pages=10,
            ):
                print("Historical:", match.kickoff, match.home_team, match.away_team)

            if future.data:
                detail = client.get_match(future.data[0].id).data
                if detail and detail.availability:
                    elo_status = detail.availability.get("ratings.elo_home")
                    if elo_status == "starter_required":
                        print("Home ELO is reserved for Starter on this payload.")
                    else:
                        print("Home ELO availability:", elo_status)
    except ForesportiaRateLimitError as exc:
        print(f"Rate limited; retry after {exc.retry_after or 'an unspecified number of'} seconds.")
    except ForesportiaAPIError as exc:
        # Normal business errors include competition_not_selected,
        # history_window_exceeded, and bulk_limit_exceeded.
        print(f"API error: HTTP {exc.status_code}, code={exc.error_code}")


if __name__ == "__main__":
    main()
