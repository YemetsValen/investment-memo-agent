"""Tests for rule-based risk detection."""

from src.agents.risk import _check_rules
from src.models.memo import RiskLevel


def test_no_flags_for_healthy_company():
    data = {
        "pe_ratio": 20,
        "debt_to_equity": 50,
        "profit_margin": 0.15,
        "current_ratio": 2.0,
        "beta": 1.1,
        "revenue_growth": 0.08,
        "earnings_growth": 0.10,
        "price_to_book": 3.0,
    }
    flags = _check_rules(data)
    assert len(flags) == 0


def test_high_pe_flag():
    data = {"pe_ratio": 55}
    flags = _check_rules(data)
    assert any(f.category == "Valuation" and f.level == RiskLevel.HIGH for f in flags)


def test_critical_debt():
    data = {"debt_to_equity": 250}
    flags = _check_rules(data)
    assert any(f.level == RiskLevel.CRITICAL for f in flags)


def test_high_debt_not_critical():
    data = {"debt_to_equity": 150}
    flags = _check_rules(data)
    assert any(f.category == "Debt" and f.level == RiskLevel.HIGH for f in flags)
    assert not any(f.level == RiskLevel.CRITICAL for f in flags)


def test_negative_margin():
    data = {"profit_margin": -0.05}
    flags = _check_rules(data)
    assert any(f.category == "Profitability" for f in flags)


def test_low_current_ratio():
    data = {"current_ratio": 0.7}
    flags = _check_rules(data)
    assert any(f.category == "Liquidity" for f in flags)


def test_high_beta():
    data = {"beta": 2.5}
    flags = _check_rules(data)
    assert any(f.category == "Volatility" for f in flags)


def test_revenue_decline():
    data = {"revenue_growth": -0.15}
    flags = _check_rules(data)
    assert any(f.category == "Growth" for f in flags)


def test_multiple_flags():
    data = {
        "pe_ratio": 60,
        "debt_to_equity": 300,
        "profit_margin": -0.10,
        "current_ratio": 0.5,
        "beta": 3.0,
    }
    flags = _check_rules(data)
    assert len(flags) >= 4
    categories = {f.category for f in flags}
    assert "Valuation" in categories
    assert "Debt" in categories
    assert "Profitability" in categories
    assert "Liquidity" in categories


def test_none_values_ignored():
    data = {"pe_ratio": None, "debt_to_equity": None}
    flags = _check_rules(data)
    assert len(flags) == 0
