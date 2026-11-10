---
name: dedupe
track: bonus
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, item_count, removed_count, removed]
side_effect: false
---
# dedupe

Removes duplicate items from already-collected results (for example the same
article returned by both `lookup` and `social_search`) before they are passed
to `format`. It does not fetch data.

Two items are duplicates when they have the same normalized URL (case-insensitive
host, no `www.`, no `#fragment`, no trailing slash, no `utm_*` / `fbclid` tracking
params). Items without a URL are compared by accent-insensitive title. The first
occurrence is kept and the original order is preserved.

Bad input (`items` is not a list) returns an error dict instead of raising.
