# src/membership.py

def calculate_monthly_fee(plan_type: str, has_discount: bool = False) -> float:
    """
    Calcula el valor mensual según el tipo de plan.
    plan_type: "basic", "premium", "vip"
    has_discount: si aplica un 10% de descuento
    """
    base_prices = {
        "basic": 20.0,
        "premium": 35.0,
        "vip": 50.0
    }

    if plan_type not in base_prices:
        raise ValueError("Plan no válido")

    price = base_prices[plan_type]

    if has_discount:
        price *= 0.9  # 10% descuento

    return round(price, 2)
