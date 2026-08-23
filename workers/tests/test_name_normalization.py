from trading_workers.ingest.name_normalization import normalize_politician_name


def test_plain_name():
    assert normalize_politician_name("Nancy Pelosi") == "nancy pelosi"


def test_last_comma_first_format():
    assert normalize_politician_name("Pelosi, Nancy") == "nancy pelosi"


def test_strips_titles_and_punctuation():
    assert normalize_politician_name("Hon. Nancy Pelosi") == "nancy pelosi"


def test_strips_suffix():
    assert normalize_politician_name("Robert Wittman III") == "robert wittman"


def test_case_insensitive():
    assert normalize_politician_name("NANCY PELOSI") == normalize_politician_name("nancy pelosi")
