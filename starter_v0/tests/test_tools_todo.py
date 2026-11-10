"""TODO(student): Tool Unit Test Challenge.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS
from tools.wiki_summary.tool import wiki_summary

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = TOOL_FUNCTIONS["clarify"](
        question="Tài khoản nào?", response_type="choice", options=["A", "B"],
    )
    assert result["options"] == ["A", "B"]
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "x1", "section": "A"},
        {"title": "y1", "section": "B"},
        {"title": "x2", "section": "A"},
    ]
    md = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    items = [{"title": "one"}, {"title": "two"}, {"title": "three"}]
    md = TOOL_FUNCTIONS["format"](items=items, template="thread")["markdown"]
    assert md.startswith("1/ ")
    assert "\n\n2/ " in md
    assert "3/ " in md


def test_format_empty_items_does_not_crash() -> None:
    for items in (None, []):
        result = TOOL_FUNCTIONS["format"](items=items, template="brief")
        assert result["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- policy ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    pytest.skip(TODO)


# ---------------- wiki_summary (tool nhóm tự viết) ----------------

def test_wiki_summary_happy_path_requests_page_and_maps_fields(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Hà Nội", "extract": "Thủ đô...",
        "content_urls": {"desktop": {"page": "https://vi.wikipedia.org/wiki/Hà_Nội"}},
    }))
    result = wiki_summary(title="Hà Nội", lang="vi")
    assert calls[0]["url"] == "https://vi.wikipedia.org/api/rest_v1/page/summary/Hà_Nội"
    assert result == {
        "title": "Hà Nội", "summary": "Thủ đô...",
        "url": "https://vi.wikipedia.org/wiki/Hà_Nội",
    }


def test_wiki_summary_bad_input_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert wiki_summary(title="   ")["error"] == "ValueError"
    assert wiki_summary(title="Hà Nội", lang="fr")["error"] == "ValueError"
    assert calls == []


def test_wiki_summary_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert wiki_summary(title="Hà Nội")["error"] == "HTTPError"