---
name: current_time
track: bonus
kind: local_formatter
requires_env: []
inputs: [timezone]
outputs: [iso, date, time, weekday_vi, weekday_en, utc_offset]
side_effect: false
---
# current_time

Returns the current date, time and weekday. `timezone` is an IANA name such as
`Asia/Ho_Chi_Minh` (default) or an offset such as `UTC+7`. Use it when the answer
depends on today's date (for example "hôm nay", "tuần này") or when a digest needs a date.

If the OS has no timezone database (common on Windows without `tzdata`), a few common
zones and every `UTC±H` offset still work. An unknown timezone returns an error dict
instead of raising.
