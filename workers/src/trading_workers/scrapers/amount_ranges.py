import re

_NUMBER = re.compile(r"[\d,]+(?:\.\d+)?")

# STOCK Act disclosures never report an exact dollar figure, only a bracket.
# This is the largest bracket used by both House and Senate disclosures.
UNBOUNDED_MAX = 50_000_000.0


def parse_amount_range(raw: str) -> tuple[float, float]:
    """Parse a STOCK Act disclosure amount string into (min, max) dollars.

    Handles the two shapes these disclosures use: a bounded range like
    "$1,001 - $15,000", and an open-ended top bracket like
    "Over $50,000,000".
    """
    numbers = [float(match.replace(",", "")) for match in _NUMBER.findall(raw)]

    if "over" in raw.lower() and numbers:
        return numbers[0], UNBOUNDED_MAX
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return 0.0, 0.0
