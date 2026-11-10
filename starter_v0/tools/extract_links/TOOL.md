---
name: extract_links
track: bonus
kind: local_formatter
requires_env: []
inputs: [text]
outputs: [count, items]
side_effect: false
---
# extract_links

Pulls the unique URLs out of a block of text the user pasted (an email, a chat log,
a list of notes). Returns them in order of first appearance as `items` with
`title`/`url`/`source`, so they can be passed to `fetch` or `dedupe`.

It finds `http(s)://` links and bare `www.` links (normalised to `https://`), strips
trailing punctuation, and removes duplicates. It does not open any link and does not
need network access. Non-string input returns an error dict instead of raising.
