---
name: text_stats
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [text, chars_per_minute]
outputs: [words, characters, reading_minutes]
side_effect: false
---

Đếm số từ, số ký tự và ước lượng thời gian đọc của một đoạn văn bản. Không cần API key.
