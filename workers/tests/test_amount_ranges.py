from trading_workers.scrapers.amount_ranges import UNBOUNDED_MAX, parse_amount_range


def test_bounded_range():
    assert parse_amount_range("$1,001 - $15,000") == (1001.0, 15000.0)


def test_over_bracket_uses_unbounded_max():
    assert parse_amount_range("Over $50,000,000") == (50_000_000.0, UNBOUNDED_MAX)


def test_single_value():
    assert parse_amount_range("$1,000") == (1000.0, 1000.0)


def test_empty_string_is_zero():
    assert parse_amount_range("") == (0.0, 0.0)
