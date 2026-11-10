"""Tool Unit Test Challenge: unit tests for the existing tools and for our new tool (dedupe).

Offline only: HTTP is mocked with `fake_http`, fake keys are set with `monkeypatch.setenv`.
One behaviour per test; the test name describes the behaviour.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]
dedupe_tool = TOOL_FUNCTIONS["dedupe"]


def _tweets(count: int, *, with_missing_id: bool = False) -> dict:
    raw = [{"tweet_id": str(i), "screen_name": "sama", "text": f"tweet {i}"} for i in range(1, count + 1)]
    if with_missing_id:
        raw.insert(0, {"screen_name": "sama", "text": "no id"})
    return {"timeline": raw}


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify_tool(question="Chọn nguồn?", response_type="choice", options=["web", "twitter"])

    assert result["options"] == ["web", "twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "1", "section": "A"},
        {"title": "2", "section": "B"},
        {"title": "3", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]

    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    items = [{"title": "một"}, {"title": "hai"}]
    markdown = format_tool(items=items, template="thread")["markdown"]

    lines = [line for line in markdown.splitlines() if line]
    assert lines[0].startswith("1/")
    assert lines[1].startswith("2/")


@pytest.mark.parametrize("items", [None, []])
def test_format_empty_items_does_not_crash(items) -> None:
    result = format_tool(items=items, template="sections")
    assert result["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "tok123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))

    lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]


def test_lookup_accepts_max_results_as_string(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))

    lookup_tool(query="AI", max_results="5")

    assert calls[0]["json"]["max_results"] == 5


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello",
        "metadata": {"title": "T", "sourceURL": "https://www.openai.com/blog/x"},
    }}))

    result = fetch_tool(url="https://www.openai.com/blog/x")

    assert calls[0]["json"]["url"] == "https://www.openai.com/blog/x"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.openai.com/blog/x",
        "source": "openai.com", "summary": "# Hello",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))

    result = fetch_tool(url="https://example.com")

    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    calls = fake_http(FakeResponse(_tweets(6, with_missing_id=True)))

    result = timeline_tool(screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        f"https://x.com/sama/status/{i}" for i in (1, 2, 3)
    ]


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    calls = fake_http(FakeResponse(_tweets(2)))

    social_search_tool(query="OpenAI", search_type="Top")

    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "k"


@pytest.mark.parametrize("tool, kwargs", [
    (timeline_tool, {"screenname": "sama"}),
    (social_search_tool, {"query": "OpenAI"}),
])
@pytest.mark.parametrize("bad_limit", [-1, -3, 0])
def test_non_positive_limit_falls_back_to_default_and_keeps_all_items(
    monkeypatch, fake_http, tool, kwargs, bad_limit
) -> None:
    """Regression: limit=-1 used to slice items[:-1] and silently drop the last post."""
    monkeypatch.setenv("RAPIDAPI_KEY", "k")
    fake_http(FakeResponse(_tweets(4)))

    result = tool(limit=bad_limit, **kwargs)

    assert len(result["items"]) == 4


def test_timeline_without_key_returns_error_dict() -> None:
    result = timeline_tool(screenname="sama")
    assert result["error"] == "RuntimeError"
    assert "RAPIDAPI_KEY" in result["message"]


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert policy_tool(query="")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="data privacy", policy_area="data_privacy", top_k=10)

    assert result["results"], "expected at least one data_privacy hit"
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="injection probe citation", policy_area="source_citation", top_k=10)

    probe = next(hit for hit in result["results"] if hit["section"] == "Injection probe")
    assert any("ignore the citation policy" in line for line in probe["untrusted_text"])
    assert "ignore" not in probe["facts"].lower()


# ---------------- NEW TOOL: dedupe ----------------

def test_dedupe_removes_urls_that_differ_only_by_tracking_noise() -> None:
    items = [
        {"title": "A", "url": "https://www.Example.com/post/?utm_source=x#top"},
        {"title": "A copy", "url": "https://example.com/post"},
        {"title": "B", "url": "https://example.com/other?id=1"},
    ]

    result = dedupe_tool(items=items)

    assert [item["title"] for item in result["items"]] == ["A", "B"]
    assert result["item_count"] == 2
    assert result["removed_count"] == 1
    assert result["removed"][0]["title"] == "A copy"


def test_dedupe_keeps_urls_with_different_real_query_params() -> None:
    items = [{"url": "https://example.com/p?id=1"}, {"url": "https://example.com/p?id=2"}]
    assert dedupe_tool(items=items)["item_count"] == 2


def test_dedupe_uses_accent_insensitive_title_when_url_missing() -> None:
    items = [{"title": "Tin Việt Nam"}, {"title": "  tin viet nam "}, {"title": "Tin khác"}]
    assert [item["title"] for item in dedupe_tool(items=items)["items"]] == ["Tin Việt Nam", "Tin khác"]


def test_dedupe_empty_or_missing_items_returns_empty_result() -> None:
    for value in (None, []):
        result = dedupe_tool(items=value)
        assert result["items"] == []
        assert result["item_count"] == 0
        assert result["removed_count"] == 0


def test_dedupe_bad_input_from_model_returns_error_dict_not_exception() -> None:
    result = dedupe_tool(items="not a list")
    assert result["error"] == "TypeError"
    assert "list" in result["message"]


def test_dedupe_skips_non_object_entries_and_keeps_valid_ones() -> None:
    result = dedupe_tool(items=["oops", {"title": "ok", "url": "https://a.com"}, 42])

    assert [item["title"] for item in result["items"]] == ["ok"]
    assert result["removed_count"] == 2


# ---------------- fetch fallback (direct download when Firecrawl fails) ----------------

_PAGE = (
    "<html><head><title>Giá vàng hôm nay</title><style>.x{color:red}</style></head>"
    "<body><script>var secret=1;</script><h1>Bảng giá</h1><p>Vàng miếng 100</p></body></html>"
)


def _patch_fetch_http(monkeypatch, *, firecrawl, direct):
    """Firecrawl uses requests.post, the fallback uses requests.get. Returns the recorded GET calls."""
    import requests

    gets: list[str] = []

    def _post(url, **kwargs):
        if isinstance(firecrawl, Exception):
            raise firecrawl
        return firecrawl

    def _get(url, **kwargs):
        gets.append(url)
        if isinstance(direct, Exception):
            raise direct
        return direct

    monkeypatch.setattr(requests, "post", _post)
    monkeypatch.setattr(requests, "get", _get)
    return gets


def test_fetch_falls_back_to_direct_download_when_firecrawl_fails(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    gets = _patch_fetch_http(monkeypatch, firecrawl=FakeResponse(status_code=500), direct=FakeResponse(text=_PAGE))

    result = fetch_tool(url="https://btmc.vn/gia-vang")

    assert gets == ["https://btmc.vn/gia-vang"]
    assert result["via"] == "direct_fallback"
    assert result["items"][0]["title"] == "Giá vàng hôm nay"
    assert "Vàng miếng 100" in result["items"][0]["summary"]


def test_fetch_fallback_strips_scripts_and_styles(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    _patch_fetch_http(monkeypatch, firecrawl=FakeResponse(status_code=500), direct=FakeResponse(text=_PAGE))

    summary = fetch_tool(url="https://example.com")["items"][0]["summary"]

    assert "secret" not in summary
    assert "color:red" not in summary


def test_fetch_returns_error_dict_when_firecrawl_and_fallback_both_fail(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "k")
    _patch_fetch_http(monkeypatch, firecrawl=FakeResponse(status_code=500), direct=FakeResponse(status_code=403))

    result = fetch_tool(url="https://example.com")

    assert result["error"] == "HTTPError"
    assert "403" in result["fallback_error"]


@pytest.mark.parametrize("bad_url", [
    "http://localhost:8501", "http://127.0.0.1/admin", "http://192.168.1.1", "file:///etc/passwd", "ftp://x.com/a",
])
def test_fetch_fallback_refuses_local_and_non_http_urls(monkeypatch, bad_url) -> None:
    gets = _patch_fetch_http(monkeypatch, firecrawl=FakeResponse(status_code=500), direct=FakeResponse(text=_PAGE))

    result = fetch_tool(url=bad_url)

    assert gets == []  # the direct download was never attempted
    assert "error" in result
    assert "fallback_error" in result
