# tests/test_membership.py
import pytest
from src.membership import calculate_monthly_fee

def test_basic_without_discount():
    assert calculate_monthly_fee("basic", False) == 20.0

def test_basic_with_discount():
    assert calculate_monthly_fee("basic", True) == 18.0

def test_premium_without_discount():
    assert calculate_monthly_fee("premium", False) == 35.0

def test_vip_with_discount():
    assert calculate_monthly_fee("vip", True) == 45.0

def test_invalid_plan_raises_error():
    with pytest.raises(ValueError):
        calculate_monthly_fee("gold", False)
