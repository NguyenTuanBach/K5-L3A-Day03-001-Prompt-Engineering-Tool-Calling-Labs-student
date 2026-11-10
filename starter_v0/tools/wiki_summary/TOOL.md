---
name: wiki_summary
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [title, summary, url]
side_effect: false
---

Lấy đoạn tóm tắt một bài Wikipedia. Không cần API key.
