"""Unit tests for our three new tools: current_time, extract_links, cite_source.

Offline and deterministic: current_time uses a fixed clock (tools.current_time.tool._now_utc is patched).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

import tools.current_time.tool as current_time_module
from tools import TOOL_FUNCTIONS

current_time_tool = TOOL_FUNCTIONS["current_time"]
extract_links_tool = TOOL_FUNCTIONS["extract_links"]
cite_source_tool = TOOL_FUNCTIONS["cite_source"]

# Tuesday 2026-11-10 03:30 UTC  ->  10:30 in Vietnam (UTC+7)
FIXED_NOW = datetime(2026, 11, 10, 3, 30, tzinfo=timezone.utc)


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(current_time_module, "_now_utc", lambda: FIXED_NOW)


# ---------------- current_time ----------------

def test_current_time_defaults_to_vietnam_time(fixed_clock) -> None:
    result = current_time_tool()

    assert result["timezone"] == "Asia/Ho_Chi_Minh"
    assert result["date"] == "2026-11-10"
    assert result["time"] == "10:30"
    assert result["weekday_vi"] == "Thứ Ba"
    assert result["weekday_en"] == "Tuesday"
    assert result["utc_offset"] == "+07:00"
    assert result["iso"].startswith("2026-11-10T10:30:00")


@pytest.mark.parametrize("zone, expected_time, expected_date, expected_offset", [
    ("UTC", "03:30", "2026-11-10", "+00:00"),
    ("UTC+7", "10:30", "2026-11-10", "+07:00"),
    ("UTC-5", "22:30", "2026-11-09", "-05:00"),     # previous day
    ("GMT+5:30", "09:00", "2026-11-10", "+05:30"),
    ("UTC+14", "17:30", "2026-11-10", "+14:00"),
])
def test_current_time_supports_utc_offsets_without_a_timezone_database(
    fixed_clock, zone, expected_time, expected_date, expected_offset
) -> None:
    result = current_time_tool(timezone=zone)

    assert result["time"] == expected_time
    assert result["date"] == expected_date
    assert result["utc_offset"] == expected_offset


@pytest.mark.parametrize("bad_zone", ["Mars/Olympus", "UTC+99", "UTC+5:99", "not a zone"])
def test_current_time_unknown_timezone_returns_error_dict_not_exception(fixed_clock, bad_zone) -> None:
    result = current_time_tool(timezone=bad_zone)

    assert result["error"] == "ValueError"
    assert "timezone" in result["message"].lower() or "offset" in result["message"].lower()


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_current_time_blank_timezone_falls_back_to_default(fixed_clock, empty) -> None:
    assert current_time_tool(timezone=empty)["timezone"] == "Asia/Ho_Chi_Minh"


# ---------------- extract_links ----------------

def test_extract_links_returns_unique_links_in_order_of_first_appearance() -> None:
    text = "Xem https://openai.com/blog/a và https://blog.google/gemini, rồi lại https://openai.com/blog/a nữa."

    result = extract_links_tool(text=text)

    assert result["count"] == 2
    assert [item["url"] for item in result["items"]] == ["https://openai.com/blog/a", "https://blog.google/gemini"]
    assert result["items"][0]["source"] == "openai.com"


def test_extract_links_strips_wrapping_punctuation_but_keeps_parentheses_inside_urls() -> None:
    text = "(xem https://a.com/x), hoặc https://en.wikipedia.org/wiki/Foo_(bar). Hết!"

    urls = [item["url"] for item in extract_links_tool(text=text)["items"]]

    assert urls == ["https://a.com/x", "https://en.wikipedia.org/wiki/Foo_(bar)"]


def test_extract_links_normalises_bare_www_links_and_deduplicates_trailing_slash() -> None:
    text = "www.anthropic.com/news và https://www.anthropic.com/news/ và HTTPS://WWW.ANTHROPIC.COM/NEWS"

    result = extract_links_tool(text=text)

    assert result["count"] == 1
    assert result["items"][0]["url"] == "https://www.anthropic.com/news"


@pytest.mark.parametrize("text", ["", "không có link nào ở đây", None, "http://", "see http://nodomain now"])
def test_extract_links_without_real_links_returns_empty_result(text) -> None:
    result = extract_links_tool(text=text)

    assert result["count"] == 0
    assert result["items"] == []


@pytest.mark.parametrize("bad", [123, ["https://a.com"], {"text": "x"}])
def test_extract_links_non_string_input_returns_error_dict(bad) -> None:
    result = extract_links_tool(text=bad)

    assert result["error"] == "TypeError"


def test_extract_links_caps_the_number_of_links() -> None:
    text = " ".join(f"https://site{i}.com/p" for i in range(80))

    assert extract_links_tool(text=text)["count"] == 50


# ---------------- cite_source ----------------

def test_cite_source_markdown_with_author_and_date() -> None:
    result = cite_source_tool(title="GPT-5 Launch", url="https://openai.com/blog/gpt-5", author="OpenAI", date="2026-01-05")

    assert result["style"] == "markdown"
    assert result["citation"] == "[GPT-5 Launch](https://openai.com/blog/gpt-5) - OpenAI, 2026-01-05"
    assert result["source"] == "openai.com"


def test_cite_source_apa_style_uses_author_date_title_domain_url() -> None:
    result = cite_source_tool(
        title="GPT-5 Launch", url="https://www.openai.com/blog/gpt-5", author="OpenAI", date="2026-01-05", style="apa"
    )

    assert result["citation"] == "OpenAI. (2026-01-05). GPT-5 Launch. openai.com. https://www.openai.com/blog/gpt-5"


def test_cite_source_apa_without_author_or_date_falls_back_to_domain_and_nd() -> None:
    result = cite_source_tool(title="Gemini", url="https://blog.google/gemini", style="apa")

    assert result["citation"] == "blog.google. (n.d.). Gemini. blog.google. https://blog.google/gemini"


def test_cite_source_missing_title_uses_domain_and_brackets_in_title_are_escaped() -> None:
    no_title = cite_source_tool(url="https://blog.google/gemini")
    bracketed = cite_source_tool(title="Tin [nóng] hôm nay", url="https://a.com/x")

    assert no_title["citation"] == "[blog.google](https://blog.google/gemini)"
    assert bracketed["citation"] == "[Tin (nóng) hôm nay](https://a.com/x)"


def test_cite_source_plain_style() -> None:
    result = cite_source_tool(title="Gemini", url="https://blog.google/gemini", date="2026", style="plain")

    assert result["citation"] == "Gemini - blog.google - 2026 - https://blog.google/gemini"


@pytest.mark.parametrize("bad_url", ["", "   ", "openai.com/blog", "ftp://a.com/x", "javascript:alert(1)", "https://"])
def test_cite_source_rejects_invalid_urls_with_error_dict(bad_url) -> None:
    result = cite_source_tool(title="x", url=bad_url)

    assert result["error"] == "ValueError"
    assert "http" in result["message"]


def test_cite_source_unknown_style_returns_error_dict_listing_valid_styles() -> None:
    result = cite_source_tool(title="x", url="https://a.com", style="chicago")

    assert result["error"] == "ValueError"
    assert "markdown" in result["message"] and "apa" in result["message"]
