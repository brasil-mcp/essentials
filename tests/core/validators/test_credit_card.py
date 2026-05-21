import json
from pathlib import Path

import pytest

from brasil_mcp.core.validators.credit_card import validate_credit_card

_FIXTURES = json.loads(
    (Path(__file__).parents[2] / "fixtures/validators/credit_card.json").read_text()
)


@pytest.mark.parametrize("case", _FIXTURES["valid"])
def test_valid_card(case: dict):
    result = validate_credit_card(case["input"])
    assert result.valid is True
    assert result.error is None
    assert result.formatted is not None
    assert result.extras.get("brand") == case["brand"]


@pytest.mark.parametrize("case", _FIXTURES["invalid"])
def test_invalid_card(case: dict):
    result = validate_credit_card(case["input"])
    assert result.valid is False
    assert result.error is not None
    assert str(result.error.code) == case["code"]


def test_formatted_idempotent():
    r1 = validate_credit_card("4111111111111111")
    assert r1.valid
    assert r1.formatted == "4111 1111 1111 1111"
    r2 = validate_credit_card(r1.formatted)
    assert r2.valid
    assert r2.extras["brand"] == "visa"


def test_unknown_brand_still_valid_if_luhn_passes():
    # Construct a number with valid Luhn but unrecognized brand.
    # 12-digit starting with 8.
    # Build with Luhn fix:
    base = "80000000000"  # 11 digits
    # Need to compute DV manually here to keep test self-contained.
    s = 0
    for i, c in enumerate(reversed(base)):
        d = int(c)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        s += d
    dv = (10 - s % 10) % 10
    num = base + str(dv)
    r = validate_credit_card(num)
    assert r.valid is True
    assert r.extras["brand"] is None


def test_diners_36_prefix_14_digits():
    """Lines 100-101: Diners Club starting with '36', length 14."""
    # 36000000000008 is Luhn-valid.
    r = validate_credit_card("36000000000008")
    assert r.valid is True
    assert r.extras["brand"] == "diners"


def test_diners_38_prefix_14_digits():
    """Lines 100-101: Diners Club starting with '38', length 14."""
    # 38000000000006 is Luhn-valid.
    r = validate_credit_card("38000000000006")
    assert r.valid is True
    assert r.extras["brand"] == "diners"


def test_14_digit_non_diners_non_jcb_falls_through():
    """Branch 100->104: length 14, prefix not in 36/38 and not 300-305 — falls
    through past the Diners check to the JCB/None path. brand should be None.
    """
    # 70000000000005 — 14 digits, prefix '70', Luhn-valid.
    r = validate_credit_card("70000000000005")
    assert r.valid is True
    assert r.extras["brand"] is None
