---
name: cite_source
track: bonus
kind: local_formatter
requires_env: []
inputs: [title, url, author, date, style]
outputs: [citation, style, source]
side_effect: false
---
# cite_source

Builds a single citation line for a source the user already gave (title, URL, optional
author and date). Styles: `markdown` (default), `apa` (a simplified APA-like line) and
`plain`. It does not fetch the page and does not verify that the details are correct.

`url` must be a full http(s) link, and `style` must be one of the three styles; otherwise
the tool returns an error dict instead of raising. A missing title falls back to the
domain name.
