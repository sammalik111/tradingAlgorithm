import re

_TITLES = {"hon", "sen", "senator", "rep", "representative", "mr", "mrs", "ms", "dr"}
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
_NON_ALNUM = re.compile(r"[^a-z0-9 ]")
_WHITESPACE = re.compile(r"\s+")


def normalize_politician_name(full_name: str) -> str:
    """Collapse the same person's name as written across different data
    sources ("Hon. Nancy Pelosi", "Pelosi, Nancy", "NANCY PELOSI") into one
    stable key, so trades from every source resolve to the same
    `Politician` row instead of creating duplicates.
    """
    normalized = full_name.lower()
    if "," in normalized:
        last, _, first = normalized.partition(",")
        normalized = f"{first.strip()} {last.strip()}"

    normalized = _NON_ALNUM.sub(" ", normalized)
    tokens = [t for t in _WHITESPACE.split(normalized) if t]
    tokens = [t for t in tokens if t not in _TITLES and t not in _SUFFIXES]
    return " ".join(tokens)
