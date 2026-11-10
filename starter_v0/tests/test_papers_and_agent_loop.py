"""Extra unit tests: arXiv tools (`papers`, `paper_text`) and the agent loop in chat.py.

Offline only. HTTP is mocked, and arXiv's built-in 3-second rate-limit waits are disabled
so the suite stays fast.
"""
from __future__ import annotations

import pytest
import requests

import chat
import tools.paper_text.tool as paper_text_module
import tools.papers.tool as papers_module
from conftest import FakeResponse
from providers.base import ModelResponse, ToolCall
from tools import TOOL_FUNCTIONS

papers_tool = TOOL_FUNCTIONS["papers"]
paper_text_tool = TOOL_FUNCTIONS["paper_text"]

ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>42</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/1706.03762v7</id>
    <title>Attention Is
      All You Need</title>
    <summary>The dominant   sequence
      transduction models.</summary>
    <published>2017-06-12T17:57:34Z</published>
    <updated>2023-08-02T00:41:18Z</updated>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.LG"/>
  </entry>
</feed>"""


@pytest.fixture(autouse=True)
def no_arxiv_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove arXiv's polite delays (rate limit + 429 back-off) so tests do not sleep."""
    monkeypatch.setattr(papers_module, "_rate_limit_arxiv", lambda: None)
    monkeypatch.setattr(paper_text_module, "_rate_limit_arxiv", lambda: None)
    monkeypatch.setattr(papers_module.time, "sleep", lambda seconds: None)


# ---------------- papers ----------------

def test_papers_maps_atom_entry_and_builds_query(fake_http) -> None:
    calls = fake_http(FakeResponse(text=ATOM_XML))

    result = papers_tool(query="AI agent evaluation", max_results=3, sort_by="submittedDate")

    params = calls[0]["params"]
    assert calls[0]["url"] == "https://export.arxiv.org/api/query"
    assert params["search_query"] == "all:AI AND all:agent AND all:evaluation"
    assert params["max_results"] == 3
    assert params["sortBy"] == "submittedDate"
    assert "User-Agent" in calls[0]["headers"]

    assert result["total_results"] == 42
    item = result["items"][0]
    assert item["arxiv_id"] == "1706.03762v7"
    assert item["title"] == "Attention Is All You Need"  # newline collapsed
    assert item["summary"] == "The dominant sequence transduction models."
    assert item["authors"] == ["Ashish Vaswani", "Noam Shazeer"]
    assert item["pdf_url"] == "http://arxiv.org/pdf/1706.03762v7"
    assert item["primary_category"] == "cs.CL"
    assert item["categories"] == ["cs.CL", "cs.LG"]


@pytest.mark.parametrize("max_results, expected", [(99, 10), (-4, 1), ("3", 3), (None, 5)])
def test_papers_clamps_max_results(fake_http, max_results, expected) -> None:
    calls = fake_http(FakeResponse(text=ATOM_XML))

    papers_tool(query="rag", max_results=max_results)

    assert calls[0]["params"]["max_results"] == expected


def test_papers_unknown_sort_by_falls_back_to_relevance(fake_http) -> None:
    calls = fake_http(FakeResponse(text=ATOM_XML))

    papers_tool(query="rag", sort_by="popularity")

    assert calls[0]["params"]["sortBy"] == "relevance"


def test_papers_retries_after_http_429_then_succeeds(monkeypatch) -> None:
    responses = [FakeResponse(status_code=429), FakeResponse(text=ATOM_XML)]
    seen: list[str] = []

    def _get(url, **kwargs):
        seen.append(url)
        return responses.pop(0)

    monkeypatch.setattr(requests, "get", _get)

    result = papers_tool(query="rag")

    assert len(seen) == 2
    assert result["items"][0]["arxiv_id"] == "1706.03762v7"


def test_papers_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=500))
    assert papers_tool(query="rag")["error"] == "HTTPError"


def test_papers_malformed_xml_returns_error_dict_not_exception(fake_http) -> None:
    fake_http(FakeResponse(text="<feed><entry>"))
    assert papers_tool(query="rag")["error"] == "ParseError"


# ---------------- paper_text ----------------

class _PdfResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int = 8192):
        yield b"%PDF-fake"


def test_paper_text_invalid_id_returns_error_and_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse())

    result = paper_text_tool(arxiv_url="not-an-arxiv-id")

    assert result["error"] == "ValueError"
    assert calls == []


def test_paper_text_accepts_abs_url_and_truncates_to_max_chars(monkeypatch, tmp_path) -> None:
    requested: list[str] = []
    monkeypatch.setattr(paper_text_module, "ARXIV_DIR", tmp_path)
    monkeypatch.setattr(requests, "get", lambda url, **kw: requested.append(url) or _PdfResponse())
    monkeypatch.setattr(paper_text_module, "_extract_pdf_text", lambda path, max_pages: ("y" * 5000, 12))

    result = paper_text_tool(arxiv_url="https://arxiv.org/abs/1706.03762v5", max_pages=2, max_chars=2000)

    assert requested == ["https://arxiv.org/pdf/1706.03762v5.pdf"]
    assert result["arxiv_id"] == "1706.03762v5"
    assert result["chars_returned"] == 2000
    assert result["page_count"] == 12
    assert result["pages_read"] == 2
    assert len(result["items"][0]["summary"]) == 2000
    assert (tmp_path / "1706.03762v5.txt").read_text(encoding="utf-8") == "y" * 2000


def test_paper_text_max_chars_has_a_floor_of_1000(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paper_text_module, "ARXIV_DIR", tmp_path)
    monkeypatch.setattr(requests, "get", lambda url, **kw: _PdfResponse())
    monkeypatch.setattr(paper_text_module, "_extract_pdf_text", lambda path, max_pages: ("z" * 5000, 3))

    result = paper_text_tool(arxiv_url="1706.03762", max_chars=10)

    assert result["chars_returned"] == 1000


def test_paper_text_download_failure_returns_error_dict(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(paper_text_module, "ARXIV_DIR", tmp_path)

    def _boom(url, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(requests, "get", _boom)

    assert paper_text_tool(arxiv_url="1706.03762")["error"] == "ConnectionError"


# ---------------- agent loop (chat.run_model_tool_loop) ----------------

class ScriptedProvider:
    """Returns the scripted responses in order and records the messages it was given."""

    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)
        self.seen_messages: list[list[dict]] = []

    def complete(self, messages, tools=None, *, model=None, temperature=0.0, tool_choice=None) -> ModelResponse:
        self.seen_messages.append(list(messages))
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


def _run(provider, max_rounds: int = 4) -> dict:
    return chat.run_model_tool_loop(
        provider=provider,
        messages=[{"role": "user", "content": "hi"}],
        tools=[],
        model=None,
        max_tool_rounds=max_rounds,
    )


def test_loop_returns_answer_when_model_calls_no_tool() -> None:
    result = _run(ScriptedProvider([ModelResponse(text="xin chào")]))

    assert result["status"] == "answered"
    assert result["assistant_text"] == "xin chào"
    assert result["tool_events"] == []


def test_loop_pauses_for_user_when_clarify_is_called_and_stops_calling_the_model() -> None:
    provider = ScriptedProvider([
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Tài khoản nào?", "response_type": "text"})]),
        ModelResponse(text="should never be reached"),
    ])

    result = _run(provider)

    assert result["status"] == "waiting_for_user"
    assert result["assistant_text"] == "Tài khoản nào?"
    assert len(provider.seen_messages) == 1


def test_loop_feeds_tool_results_back_to_the_model() -> None:
    provider = ScriptedProvider([
        ModelResponse(tool_calls=[ToolCall("dedupe", {"items": [{"url": "https://a.com"}, {"url": "https://a.com/"}]})]),
        ModelResponse(text="đã bỏ 1 tin trùng"),
    ])

    result = _run(provider)

    assert result["status"] == "answered"
    assert len(provider.seen_messages) == 2
    fed_back = provider.seen_messages[1][-1]["content"]
    assert fed_back.startswith("TOOL_RESULTS_JSON")
    assert '"removed_count": 1' in fed_back


def test_loop_stops_at_max_tool_rounds_when_model_keeps_calling_tools() -> None:
    provider = ScriptedProvider([ModelResponse(tool_calls=[ToolCall("dedupe", {"items": []})])])

    result = _run(provider, max_rounds=2)

    assert result["status"] == "max_tool_rounds"
    assert len(provider.seen_messages) == 2


def test_execute_tool_call_unknown_tool_returns_error_dict() -> None:
    event = chat.execute_tool_call(ToolCall("made_up_tool", {}))
    assert event["result"]["error"] == "unknown_tool"


def test_execute_tool_call_bad_arguments_return_error_dict_instead_of_raising() -> None:
    event = chat.execute_tool_call(ToolCall("dedupe", {"not_a_param": 1}))
    assert event["result"]["error"] == "TypeError"


@pytest.mark.parametrize("window, expected_len", [(0, 0), (-1, 0), (1, 2), (2, 4), (10, 6)])
def test_trim_history_keeps_last_n_user_assistant_pairs(window, expected_len) -> None:
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(6)]

    trimmed = chat.trim_history(history, window)

    assert len(trimmed) == expected_len
    if expected_len:
        assert trimmed[-1]["content"] == "5"
