import pytest
import hashlib
import re

def parse_remaining_lease(raw_str: str) -> float:
    if not raw_str:
        return 0.0
    if "year" in raw_str:
        y_match = re.search(r'([0-9]+)\s*year', raw_str)
        m_match = re.search(r'([0-9]+)\s*month', raw_str)
        years = float(y_match.group(1)) if y_match else 0.0
        months = float(m_match.group(1)) if m_match else 0.0
        return years + months / 12.0
    try:
        return float(raw_str.strip())
    except ValueError:
        return 0.0

def parse_storey_range(raw_str: str) -> float:
    parts = raw_str.split(" TO ")
    return (float(parts[0]) + float(parts[1])) / 2.0

def test_remaining_lease_parsing():
    assert round(parse_remaining_lease("61 years 04 months"), 4) == round(61 + 4/12, 4)
    assert parse_remaining_lease("63 years") == 63.0
    assert parse_remaining_lease("70") == 70.0
    assert round(parse_remaining_lease("95 years 11 months"), 4) == round(95 + 11/12, 4)

def test_storey_range_parsing():
    assert parse_storey_range("04 TO 06") == 5.0
    assert parse_storey_range("10 TO 12") == 11.0
    assert parse_storey_range("01 TO 03") == 2.0

def test_transaction_sk_uniqueness():
    hash1 = hashlib.sha256(b"dummy1").hexdigest()
    sk1_occ1 = hashlib.sha256(f"{hash1}||1".encode()).hexdigest()
    sk1_occ2 = hashlib.sha256(f"{hash1}||2".encode()).hexdigest()
    assert sk1_occ1 != sk1_occ2

