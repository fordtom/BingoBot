import asyncio
import importlib.util
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PARSER_PATH = os.path.join(BASE_DIR, "bingo", "utils", "csv_parser.py")

spec = importlib.util.spec_from_file_location("csv_parser", CSV_PARSER_PATH)
csv_parser = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = csv_parser
spec.loader.exec_module(csv_parser)

parse_events_csv = csv_parser.parse_events_csv


def test_parse_events_with_header():
    csv_content = "description\nEvent 1\nEvent 2\n"
    expected = [
        {"description": "Event 1"},
        {"description": "Event 2"},
    ]
    result = asyncio.run(parse_events_csv(csv_content))
    assert result == expected


def test_parse_events_without_header():
    csv_content = "Event A\nEvent B\n"
    expected = [
        {"description": "Event A"},
        {"description": "Event B"},
    ]
    result = asyncio.run(parse_events_csv(csv_content))
    assert result == expected

