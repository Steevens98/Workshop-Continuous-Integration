import pytest

from gym_membership.pricing import calculate_total


def test_single_member_basic_no_addons():
    r = calculate_total(members=1, plan_code="basic")
    assert r.total_usd == 60
    assert r.group_discount_usd == 0
    assert r.premium_surcharge_usd == 0
    assert r.special_offer_discount_usd == 0


def test_group_discount_applies_for_two_members():
    # 2 * 60 = 120, discount 10% => 12, total => 108
    r = calculate_total(members=2, plan_code="basic")
    assert r.base_total_usd == 120
    assert r.group_discount_usd == 12
    assert r.total_usd == 108


def test_special_offer_200_threshold_strictly_exceeds():
    # 2 members premium: 2 * 100 = 200 => does NOT exceed 200
    r = calculate_total(members=2, plan_code="premium")
    assert r.base_total_usd == 200
    assert r.special_offer_discount_usd == 0


def test_special_offer_over_200_gets_20():
    # 3 members basic: 3*60=180, group discount 10% => 18 => 162 (not >200)
    # Add personal training: +60 per member => 3*(60+60)=360, group discount => 36 => 324 => >200 => -20 => 304
    r = calculate_total(members=3, plan_code="basic", addon_codes=["pt"])
    assert r.base_total_usd == 360
    assert r.group_discount_usd == 36
    assert r.premium_surcharge_usd == 0
    assert r.special_offer_discount_usd == 20
    assert r.total_usd == 304


def test_special_offer_over_400_gets_50():
    # 4 members family with pt:
    # per member = 160 + 60 = 220 => base 880
    # group -10% => 88 => 792
    # no premium => 792
    # >400 => -50 => 742
    r = calculate_total(members=4, plan_code="family", addon_codes=["pt"])
    assert r.base_total_usd == 880
    assert r.group_discount_usd == 88
    assert r.special_offer_discount_usd == 50
    assert r.total_usd == 742


def test_premium_surcharge_15_percent_after_group_discount():
    # 2 members premium + exclusive:
    # per member = 100 + 80 = 180 => base 360
    # group -10% => 36 => 324
    # premium surcharge +15% => 48 (15% of 324 = 48.6 but integer math? Here should be exact with our multiples: 324*15/100 = 48.6
    # OOPS: 324 is not multiple of 20. That's why we used multiples of 20 for raw amounts, but discounts can create non-multiples.
    #
    # Our implementation uses integer division // (floor). This test locks that behavior.
    # 324*15//100 = 48
    # after surcharge = 372
    # special offer? 372 > 200 => -20 => 352
    r = calculate_total(members=2, plan_code="premium", premium_codes=["exclusive"])
    assert r.base_total_usd == 360
    assert r.group_discount_usd == 36
    assert r.premium_surcharge_usd == 48
    assert r.special_offer_discount_usd == 20
    assert r.total_usd == 352


def test_invalid_members_returns_error():
    with pytest.raises(ValueError):
        calculate_total(members=0, plan_code="basic")


def test_unknown_plan_returns_error():
    with pytest.raises(ValueError):
        calculate_total(members=1, plan_code="gold")
