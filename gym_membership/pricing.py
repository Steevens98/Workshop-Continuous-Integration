from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class CatalogItem:
    code: str
    name: str
    price_usd: int
    available: bool = True
    is_premium: bool = False


@dataclass(frozen=True)
class CalculationResult:
    members: int
    plan: CatalogItem
    addons: Tuple[CatalogItem, ...]
    premium_features: Tuple[CatalogItem, ...]
    base_total_usd: int
    group_discount_usd: int
    premium_surcharge_usd: int
    special_offer_discount_usd: int
    total_usd: int
    messages: Tuple[str, ...]


# ----------------------------
# Catalog (ASSUMPTIONS)
# ----------------------------
PLANS: Dict[str, CatalogItem] = {
    "basic": CatalogItem("basic", "Basic", 60, available=True),
    "premium": CatalogItem("premium", "Premium", 100, available=True),
    "family": CatalogItem("family", "Family", 160, available=True),
}

ADDONS: Dict[str, CatalogItem] = {
    "nutrition": CatalogItem("nutrition", "Nutrition plan", 20, available=True),
    "classes": CatalogItem("classes", "Group classes", 40, available=True),
    "pt": CatalogItem("pt", "Personal training sessions", 60, available=True),
}

PREMIUM_FEATURES: Dict[str, CatalogItem] = {
    "exclusive": CatalogItem(
        "exclusive", "Exclusive facilities access", 80, available=True, is_premium=True
    ),
    "specialized": CatalogItem(
        "specialized", "Specialized training program", 120, available=True, is_premium=True
    ),
}


# ----------------------------
# Validation
# ----------------------------
def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


def validate_selection(
    members: int,
    plan_code: str,
    addon_codes: Iterable[str],
    premium_codes: Iterable[str],
) -> List[str]:
    errors: List[str] = []

    if not isinstance(members, int) or members <= 0:
        errors.append("members must be a positive integer.")

    if plan_code not in PLANS:
        errors.append(f"unknown plan: {plan_code!r}.")
    else:
        if not PLANS[plan_code].available:
            errors.append(f"plan '{plan_code}' is not available.")

    for code in _dedupe_preserve_order(addon_codes):
        if code not in ADDONS:
            errors.append(f"unknown add-on: {code!r}.")
        elif not ADDONS[code].available:
            errors.append(f"add-on '{code}' is not available.")

    for code in _dedupe_preserve_order(premium_codes):
        if code not in PREMIUM_FEATURES:
            errors.append(f"unknown premium feature: {code!r}.")
        elif not PREMIUM_FEATURES[code].available:
            errors.append(f"premium feature '{code}' is not available.")

    return errors


# ----------------------------
# Pricing rules
# ----------------------------
def _special_offer_discount(total_usd: int) -> int:
    # "exceeds $200" and "exceeds $400"
    if total_usd > 400:
        return 50
    if total_usd > 200:
        return 20
    return 0


def calculate_total(
    members: int,
    plan_code: str,
    addon_codes: Iterable[str] = (),
    premium_codes: Iterable[str] = (),
) -> CalculationResult:
    """
    Rule order (documented so tests are deterministic):
      1) base_total = members * (plan + addons + premium_features)
      2) group discount: if members >= 2 => 10% off base_total
      3) premium surcharge: if any premium feature selected => +15% on (base_total - group_discount)
      4) special offer discount based on total after surcharge:
         >200 => -20, >400 => -50
    """
    addon_codes_list = _dedupe_preserve_order(addon_codes)
    premium_codes_list = _dedupe_preserve_order(premium_codes)

    errors = validate_selection(members, plan_code, addon_codes_list, premium_codes_list)
    if errors:
        # Raise one error message to keep CLI clean; unit tests can enforce exact behavior
        raise ValueError("; ".join(errors))

    plan = PLANS[plan_code]
    addons = tuple(ADDONS[c] for c in addon_codes_list)
    premium_features = tuple(PREMIUM_FEATURES[c] for c in premium_codes_list)

    per_member = plan.price_usd + sum(a.price_usd for a in addons) + sum(
        p.price_usd for p in premium_features
    )
    base_total = members * per_member

    messages: List[str] = []
    if members >= 2:
        messages.append("Group discount applied: 10% off for 2+ members on the same plan.")

    group_discount = (base_total * 10) // 100 if members >= 2 else 0
    after_group = base_total - group_discount

    premium_surcharge = 0
    if premium_features:
        messages.append("Premium surcharge applied: +15% (premium features selected).")
        premium_surcharge = (after_group * 15) // 100

    after_surcharge = after_group + premium_surcharge

    special_offer = _special_offer_discount(after_surcharge)
    if special_offer == 20:
        messages.append("Special offer applied: -$20 (total exceeds $200).")
    elif special_offer == 50:
        messages.append("Special offer applied: -$50 (total exceeds $400).")

    total = after_surcharge - special_offer
    if total <= 0:
        raise ValueError("calculated total is not positive; check pricing configuration.")

    return CalculationResult(
        members=members,
        plan=plan,
        addons=addons,
        premium_features=premium_features,
        base_total_usd=base_total,
        group_discount_usd=group_discount,
        premium_surcharge_usd=premium_surcharge,
        special_offer_discount_usd=special_offer,
        total_usd=total,
        messages=tuple(messages),
    )
