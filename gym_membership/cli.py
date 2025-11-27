from __future__ import annotations

from typing import List

from gym_membership.pricing import ADDONS, PLANS, PREMIUM_FEATURES, calculate_total


def _read_int(prompt: str) -> int:
    raw = input(prompt).strip()
    if raw.lower() in {"q", "quit", "exit"}:
        raise KeyboardInterrupt
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError("Please enter a valid integer (or 'q' to cancel).") from exc


def _read_codes(prompt: str) -> List[str]:
    raw = input(prompt).strip()
    if raw.lower() in {"-", "none", ""}:
        return []
    if raw.lower() in {"q", "quit", "exit"}:
        raise KeyboardInterrupt
    # allow "a,b,c" or "a b c"
    parts = [p.strip() for p in raw.replace(" ", ",").split(",")]
    return [p for p in parts if p]


def _print_catalog(title: str, items: dict) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for code, item in items.items():
        status = "" if item.available else " (UNAVAILABLE)"
        print(f"  {code:12s}  ${item.price_usd:>3d}  - {item.name}{status}")
    print("  (Type codes separated by comma, '-' for none, 'q' to cancel)\n")


def run_cli() -> int:
    print("Gym Membership Management System")
    print("Type 'q' at any time to cancel.\n")

    try:
        # Members
        members = _read_int("How many members are signing up together? ")

        # Plan selection
        _print_catalog("Membership Plans", PLANS)
        plan_code = input("Choose a plan code (basic/premium/family): ").strip().lower()
        if plan_code in {"q", "quit", "exit"}:
            return -1

        # Add-ons
        _print_catalog("Add-ons (per member)", ADDONS)
        addon_codes = _read_codes("Add add-ons (e.g., nutrition,classes) or '-' for none: ")

        # Premium features
        _print_catalog("Premium features (per member)", PREMIUM_FEATURES)
        premium_codes = _read_codes("Add premium features (e.g., exclusive) or '-' for none: ")

        # Calculation + confirmation
        result = calculate_total(
            members=members,
            plan_code=plan_code,
            addon_codes=addon_codes,
            premium_codes=premium_codes,
        )

        print("\n--- SUMMARY ---")
        print(f"Members: {result.members}")
        print(f"Plan: {result.plan.name} (${result.plan.price_usd} per member)")
        if result.addons:
            print("Add-ons:")
            for a in result.addons:
                print(f"  - {a.name} (+${a.price_usd} per member)")
        else:
            print("Add-ons: none")

        if result.premium_features:
            print("Premium features:")
            for p in result.premium_features:
                print(f"  - {p.name} (+${p.price_usd} per member)")
        else:
            print("Premium features: none")

        print("\nBreakdown:")
        print(f"  Base total:              ${result.base_total_usd}")
        print(f"  Group discount:          -${result.group_discount_usd}")
        print(f"  Premium surcharge:       +${result.premium_surcharge_usd}")
        print(f"  Special offer discount:  -${result.special_offer_discount_usd}")
        print(f"  TOTAL:                   ${result.total_usd}")

        if result.messages:
            print("\nNotes:")
            for msg in result.messages:
                print(f"  * {msg}")

        confirm = input("\nConfirm purchase? (y/n): ").strip().lower()
        if confirm == "y":
            print(result.total_usd)  # required positive integer output
            return result.total_usd

        print(-1)
        return -1

    except KeyboardInterrupt:
        print("\n-1")
        return -1
    except Exception as exc:  # noqa: BLE001 (keep CLI resilient)
        print(f"\nERROR: {exc}")
        print(-1)
        return -1
