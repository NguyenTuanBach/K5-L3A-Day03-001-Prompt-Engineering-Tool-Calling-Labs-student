# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 001
- Members: Nguyễn Tuấn Bách
Võ Sỹ Thái Sơn
Trần Nguyễn Anh Phong
- Provider/model: OpenAI / gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin tức trên web, tìm bài đăng X/Twitter theo từ khóa hoặc theo tài khoản, đọc nội dung một URL, bỏ tin trùng lặp rồi tổng hợp thành bản tin. Agent **hỏi lại khi thiếu thông tin** (không tự đoán tài khoản hay URL), **chỉ gửi Telegram sau khi bạn xác nhận**, và từ chối các yêu cầu ngoài phạm vi nghiên cứu (giải toán, viết code, dịch thuật).

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận có/không trước khi gửi | không |
| timeline | lấy các bài đăng gần đây của MỘT tài khoản X/Twitter (ví dụ `sama`) | không |
| social_search | tìm bài đăng X/Twitter theo từ khóa, sắp xếp Latest hoặc Top | không |
| lookup | tìm tin tức/thông tin trên web (topic general hoặc news, theo khoảng thời gian) | không |
| fetch | đọc nội dung của một URL cụ thể | không |
| format | trình bày các item đã có thành bản tin markdown (brief, sections, bullets, thread, daily_ai_vn) | không |
| send | gửi văn bản lên kênh Telegram, chỉ khi người dùng đã xác nhận (`confirmed=true`) | không |
| policy | tra cứu chính sách nội bộ của công ty | không |
| papers | tìm bài báo khoa học trên arXiv | không |
| paper_text | tải PDF arXiv và trích nội dung text | không |
| **dedupe** | loại các item trùng lặp (cùng URL hoặc cùng tiêu đề) trước khi tạo bản tin | **có** |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. `Tin tức AI hôm nay có gì nổi bật?` → agent tìm tin trên web (`lookup`, topic news, trong ngày).
2. `Tweet mới nhất của Sam Altman là gì?` → agent đổi tên thành handle `sama` rồi lấy bài đăng (`timeline`).
3. `Mọi người đang bàn gì về GPT-5 trên Twitter?` → agent tìm bài đăng theo chủ đề (`social_search`).
4. `Tóm tắt 3 tweet mới nhất giúp mình` → thiếu tài khoản, agent **hỏi lại** thay vì đoán.
5. `Đăng bản tin này lên Telegram giúp mình` → agent **xin xác nhận** trước, không tự gửi.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
