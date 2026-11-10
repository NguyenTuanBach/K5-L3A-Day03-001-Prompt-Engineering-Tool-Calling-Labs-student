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

> Mọi số liệu dưới đây lấy từ `artifacts/version_log.csv`, `runs/*.json` và `transcripts/*.transcript.json`. Model: `gpt-4o-mini` (OpenAI), temperature 0. Metric chính là `case_accuracy` (số case đạt / tổng). "base" = 20 case cố định (`eval_base.json`), "group" = 10 case của nhóm (`eval_group.json`).

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Prompt và tools gốc của starter | — | base 0.65 (13/20) | `runs/v0_B_base_openai_20261110T095527377981.json` |
| v1 | `system_prompt.md` | Bỏ 3 chỉ dẫn xấu (đoán thay vì hỏi, gửi không xác nhận, ép một bước) thì agent ngừng đoán và biết từ chối | 0.65 | base 0.85 (17/20) | `runs/v1_B_base_openai_20261110T095755194667.json` |
| v2 | `tools.yaml` (clarify) | Mô tả `response_type` mơ hồ nên agent bỏ trống; viết rõ khi nào dùng `text` / `yes_no` | 0.85 | base 0.95 (19/20) | `runs/v2_B_base_openai_20261110T095848428329.json` |
| v3 | `system_prompt.md` | Yêu cầu gửi/đăng thì hành động đầu tiên là `clarify` yes_no | 0.95 | base 1.00 (20/20) | `runs/v3_B_base_openai_20261110T095945399500.json` |
| v4 | `tools.yaml` (mọi tool) | Description rõ (khi nào dùng / không dùng) + quy ước args giúp route ổn định hơn | 1.00 | base 0.95 (19/20), **tụt** | `runs/v4_B_base_openai_20261110T100421272782.json` |
| v5 | `system_prompt.md` | Thêm rule routing + quy tắc "đổi nguồn thì chỉ gọi tool của nguồn mới" | 0.95 | base 1.00 (20/20) | `runs/v5_B_base_openai_20261110T101025033237.json` |
| v6 | `tools.yaml` (+`dedupe`) | Thêm tool thứ 11 không làm hỏng routing cũ | base 1.00 | base 1.00; group 0.90 (9/10) | `runs/v6_B_group_openai_20261110T101930686620.json` |
| v7 | `system_prompt.md` | Thêm ngoại lệ "đã xác nhận rõ thì gửi luôn" để sửa G05 | group 0.90 | group 0.90: G05 sửa được nhưng **G09 tụt** | `runs/v7_B_group_openai_20261110T101956968414.json` |
| v8 | `system_prompt.md` | Người dùng hủy thì chỉ xác nhận bằng lời, không hỏi lại | group 0.90 | group 1.00, base 1.00 | `runs/v8_B_group_openai_20261110T102133502510.json` |
| v9 | `system_prompt.md` | Không suy ra tài khoản từ chủ đề của lượt trước (lỗi thấy ở chat live) | group 1.00 | group 1.00, base 1.00; live lượt 2 hỏi lại | `runs/v9_B_base_openai_20261110T103330500469.json` |
| v10 | `system_prompt.md` + `tools/fetch` | Mặc định trả lời tiếng Việt; `fetch` tải trực tiếp khi Firecrawl lỗi | base/group 1.00 | base 1.00, group 1.00 | `runs/v10_B_base_openai_20261110T111153364010.json` |
| v11 | `system_prompt.md` | Áp dụng đơn vị/thang đo mà nguồn nêu (ĐVT 1 = 1.000 vnđ) | base/group 1.00 | base 1.00, group 1.00; live đúng 3/3 lần | `runs/v11_B_base_openai_20261110T113023208318.json` |

Độ dao động: v5 chạy thêm 2 lần (`v5-rerun1/2`) đều 20/20. v7 chạy thêm 2 lần đều giữ group 0.90 với G09 fail (lỗi ổn định, không phải nhiễu). Lưu ý: ở v1, R03 và R13 tự pass dù không sửa gì liên quan đến chúng; nhóm coi đó là nhiễu giữa các lần chạy và **không** tính là tác dụng của v1.

## B2. Failure Analysis

Lấy từ `results[*].result.failures` và `actual_tool_calls`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama")` | Thiếu tài khoản mà agent tự đoán Sam Altman | v1: bỏ chỉ dẫn "chọn tài khoản nổi tiếng", thêm rule hỏi lại |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | Bịa URL | v1: bỏ chỉ dẫn "assume a likely URL" |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này đã được đăng...")` | Gửi ngay không xin xác nhận | v1 + v3: luôn `clarify yes_no` trước |
| R08_out_of_scope, R14_out_of_scope_coding (v0) | out_of_scope | `send(...)` chứa lời giải toán / code | Bị ép "chọn một tool" nên nhét câu trả lời vào `send` | v1: bỏ "luôn dùng một tool", thêm rule từ chối ngoài phạm vi |
| R03_web_news_routing, R13 (v0) | wrong_arg_value | `lookup(query="AI news", ...)`; R13 còn thiếu `topic` | `query` thừa chữ "news"; thiếu `topic=news` | v4: mô tả `query` ngắn, `topic=news` cho tin tức (ở v1 hai case này pass nhưng do nhiễu) |
| R10, R11, R12 (v1) | wrong_arg_value | `clarify(question=...)` không có `response_type` | Gọi đúng tool nhưng bỏ trống tham số | v2: viết rõ `response_type` trong `tools.yaml` |
| M06_switch_tool (v4) | wrong_tool | `lookup(...)` + `social_search(...)` | Đổi nguồn sang web nhưng vẫn gọi thêm tool nguồn cũ | v5: rule "đổi nguồn thì chỉ gọi tool nguồn mới" |
| G05_send_already_confirmed (v6) | wrong_boundary | `clarify(yes_no)` | Over-correction của v3: hỏi lại dù người dùng đã xác nhận | v7: thêm ngoại lệ đã xác nhận |
| G09_decline_send (v7) | unnecessary_tool | `clarify("Bạn có chắc muốn hủy?")` | Ngoại lệ của v7 làm agent hỏi lại khi người dùng hủy (fail 3/3 lần) | v8: hủy thì chỉ trả lời ngắn, không hỏi, không gọi tool |
| (chat live, v8) lượt 2 | missing_info | `timeline(screenname="OpenAI")` | Lượt 1 nói về AI nên agent suy ra tài khoản; eval đơn lượt R10 vẫn pass | v9: chỉ dùng tài khoản/URL do người dùng nêu |
| (chat live, v10) | sai số liệu | `fetch` + trả lời "13,700 VNĐ" | Bỏ qua "ĐVT 1 = 1.000 vnđ", sai gấp 1000 lần; eval không bắt được | v11: áp dụng đơn vị/thang đo của nguồn |

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 đơn lượt + 5 đa lượt), kết quả ở v11 (group 10/10; file chạy: `runs/v11_B_group_openai_20261110T113046761712.json`).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_dedupe_routing | **Tool mới**: có danh sách tin và yêu cầu bỏ tin trùng | `dedupe` | Pass |
| G02_handle_with_at | Handle viết kèm `@` | `timeline(screenname="karpathy", limit=3)` (không có `@`) | Pass |
| G03_policy_routing | Hỏi quy định nội bộ | `policy` (không phải `lookup`) | Pass |
| G04_translate_out_of_scope | Dịch thuật không thuộc research | Không gọi tool | Pass |
| G05_send_already_confirmed | Người dùng đã xác nhận rồi | `send(confirmed=true)`, không hỏi lại | Pass (v6 fail, sửa ở v7) |
| G06_clarify_then_url (2 lượt) | Lượt 1 thiếu URL, lượt 2 bổ sung | `fetch(url=...)` | Pass |
| G07_correction_name_limit (3 lượt) | Sửa tên người, đổi sang handle, limit ở lượt cuối | `timeline(screenname="demishassabis", limit=4)` | Pass |
| G08_confirm_yes_then_send (2 lượt) | Đã hỏi gửi, người dùng đồng ý | `send(confirmed=true)` | Pass |
| G09_decline_send (2 lượt) | Người dùng rút lại | Không gọi tool | Pass (v7 fail, sửa ở v8) |
| G10_switch_papers_to_web_news (3 lượt) | Đổi nguồn từ papers sang tin web | `lookup(query="RAG", topic="news", timeframe="week")` | Pass |

Giá trị của bộ case này: base eval đã bão hòa ở 1.00 từ v3, còn group eval **bắt được 2 lỗi mà base không thấy** (G05, G09) và kiểm tra được tool mới.

## B4. Live Chat Evidence

Transcript chạy bằng `chat.py` (model thật, tool thật). Hai transcript dưới đây so sánh trước và sau khi sửa lỗi đoán tài khoản.

**Transcript 1: `transcripts/v8_openai_20261110T103033460930.transcript.json` (v8)**

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v8+p9658a92659e4 | Đúng |
| 2 | Tóm tắt 3 tweet mới nhất giúp mình | `timeline(screenname="OpenAI", limit=3)` | v8 | **Sai: tự đoán tài khoản** |
| 3 | Của Sam Altman nhé | `timeline(screenname="sama", limit=3)` | v8 | Đúng |
| 4 | Đăng bản tin này lên Telegram giúp mình | `clarify(response_type="yes_no")` | v8 | Đúng: hỏi xác nhận, không gửi |

**Transcript 2: `transcripts/v9_openai_20261110T103422050909.transcript.json` (v9)**

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v9+p208817fa30a2 | Đúng |
| 2 | Tóm tắt 3 tweet mới nhất giúp mình | (không gọi tool) | v9 | Đúng: hỏi lại "tài khoản nào?" bằng câu trả lời text |
| 3 | Của Sam Altman nhé | `timeline(screenname="sama", limit=3)` | v9 | Đúng |
| 4 | Đăng bản tin này lên Telegram giúp mình | `clarify(response_type="yes_no")` | v9 | Đúng |

Lưu ý: ở v9 lượt 2, agent hỏi lại bằng text chứ không gọi tool `clarify`. Hành vi đúng với người dùng nhưng eval R10 mong đợi `clarify`, và chấm tự động không phân biệt được hai cách này.

**Chat qua UI Streamlit (không đính kèm transcript):** gửi riêng đường link `btmc.vn/gia-vang-theo-ngay.html`. Phát hiện: (1) trả lời bằng tiếng Anh, (2) Firecrawl trả lỗi 500, (3) sau khi có fallback, agent đọc sai đơn vị giá vàng. Đã sửa ở v10 và v11 (xem B1, B2). Các transcript từ UI không nộp vì bị gắn nhãn version không khớp với prompt lúc chạy.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v8_...`, `v9_...` (lượt 4); `eval_group.json` G05, G08, G09 | Agent không gửi khi chưa xác nhận, gửi `confirmed=true` khi đã xác nhận, không hỏi lại khi người dùng hủy | **Chưa gửi thật lên Telegram** (nhóm chưa tạo bot), nên chỉ có bằng chứng về hành vi hỏi/không hỏi, không có bằng chứng tin nhắn đã được gửi |
| arXiv/company policy | `eval_group.json` G03, G10 | `policy` và `papers` được route đúng | Chỉ kiểm tra routing, chưa kiểm tra chất lượng nội dung trả về |
| UI | `app.py`, `.streamlit/config.toml` | Streamlit chạy local, tự thử lại khi mạng rớt, ẩn/hiện chi tiết tool, lưu transcript cùng định dạng | Link tunnel là tạm thời, mất khi tắt `cloudflared`; ai có link đều dùng credit key của nhóm |
| Tool mới `dedupe` | `tools/dedupe/`, `tests/test_tools_todo.py` | Loại tin trùng URL (bỏ `www.`, `#fragment`, `utm_*`) hoặc trùng tiêu đề; có G01 kiểm tra routing | Nhóm chỉ thêm **1** tool mới nên **chưa** đạt điều kiện "hơn 3 tool" của điểm thưởng |
| Tool unit tests (`tests/`) | `pytest`: **128 passed, 0 skipped** | Điền hết các stub; 6 test cho `dedupe`; 8 test cho nhánh dự phòng của `fetch`; 24 test cho `papers`, `paper_text` và vòng lặp agent (`tests/test_papers_and_agent_loop.py`) | Test chạy offline, HTTP được mock, các lệnh chờ 3 giây của arXiv được tắt trong test |

**Tool unit tests, chi tiết.** Trước: 62 passed, 17 skipped. Sau: 128 passed, 0 skipped.

- **Bug tìm được trong tool có sẵn (2):**
  1. `timeline` và `social_search` nhận `limit` âm sẽ cắt `items[:-n]` và âm thầm bỏ các bài cuối (`limit=-3` chỉ trả về 1 trên 4 bài). Test được viết trước và fail 4 case, sau đó sửa `_tweets_from` để `limit < 1` quay về mặc định 5. Test được giữ lại làm regression test.
  2. `papers` không chuẩn hóa khoảng trắng của tiêu đề: tiêu đề arXiv xuống dòng kèm thụt đầu dòng nên kết quả có nhiều dấu cách liền nhau (`"Attention Is       All You Need"`), trong khi `summary` thì đã được chuẩn hóa. Lỗi chỉ ảnh hưởng hiển thị. Đã sửa bằng cách chuẩn hóa `title` giống `summary` và giữ test hồi quy.
- **Ví dụ lỗi unit test bắt được mà eval không bắt được:** model vẫn gọi đúng `timeline(limit=-1)` nên eval báo pass, nhưng người dùng nhận thiếu bài.
- **Cải tiến `fetch`:** khi Firecrawl lỗi thì tải trực tiếp và trích chữ. Có rào chắn từ chối URL không phải http(s) và IP nội bộ. Giới hạn đã biết: chỉ chặn IP trực tiếp và tên `localhost`, **không phân giải tên miền**, nên tên miền công khai trỏ vào IP nội bộ sẽ không bị chặn.
- **Hai điểm lệch nhỏ chưa sửa:** `policy(top_k=0)` trả 3 kết quả nhưng `top_k` âm trả 1 (không nhất quán); `format` để lại ký tự `-` thừa khi item không có URL.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?** Hành vi và thứ tự ưu tiên: bỏ ba chỉ dẫn xấu (v1), xin xác nhận trước khi gửi và các ngoại lệ (v3, v7, v8), rule routing và quy tắc đổi nguồn (v5), không suy ra tài khoản từ ngữ cảnh (v9), ngôn ngữ trả lời (v10), áp dụng đơn vị của nguồn (v11). Các lỗi kiểu "agent làm sai việc" và "sai thứ tự" đều nằm ở prompt.
- **Which fixes belonged in `tools.yaml`?** Các lỗi kiểu "gọi đúng tool nhưng sai tham số": mô tả `response_type` (v2), quy ước args như handle không có `@`, `topic=news`, `timeframe`, `search_type`, mô tả `send` với `confirmed=true` (v4), và khai báo tool mới `dedupe` (v6).
- **Which failure needed manual review instead of automatic grading?** (1) Việc đọc sai đơn vị giá vàng (13,700 thay vì 13.700.000): eval chỉ chấm tên tool và args nên hoàn toàn không thấy lỗi này, chỉ phát hiện khi đọc câu trả lời thật. (2) Hỏi lại bằng text so với gọi `clarify`: người dùng thấy giống nhau, eval chấm khác nhau. (3) Lỗi đoán tài khoản chỉ lộ ra khi chat nhiều lượt có ngữ cảnh, trong khi R10 đơn lượt vẫn pass.
- **What would we improve next?** Thêm eval case kiểm tra số liệu và đơn vị; chạy mỗi version nhiều lần để tách nhiễu khỏi tác dụng thật (v4 tụt điểm nhưng nhóm chưa chứng minh được là do thay đổi hay do nhiễu, chỉ biết v5 sửa được); thêm ít nhất 3 tool nữa để đạt điều kiện điểm thưởng; thử gửi Telegram thật; và thử model local.

Hạn chế cần nêu: chỉ dùng một model (`gpt-4o-mini`); bộ 30 case còn nhỏ nên 1.00 không có nghĩa agent đúng trên mọi tình huống; mỗi cấu hình chạy rất ít lần.

## B7. Small Local Model Challenge (bonus)

**Nhóm không thực hiện phần bonus này** (chưa cài Ollama, chưa chạy model local). Vì vậy bảng so sánh cloud và local, bảng lỗi đặc thù của model nhỏ, và các bản `v4-local`, `v5-local` không có số liệu để điền. Các phiên bản `v4`, `v5` trong `version_log.csv` là các vòng tối ưu cho model cloud, không liên quan đến thử thách này.
