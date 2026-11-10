---
name: fetch
track: core
kind: live_api
provider: Firecrawl
requires_env: [FIRECRAWL_API_KEY]
inputs: [url]
outputs: [items]
side_effect: false
---
# fetch

Reads the content of a single URL via Firecrawl.

If Firecrawl fails for a page (for example HTTP 500 or a blocked site), the tool
falls back to a plain download and extracts the visible text (`via: direct_fallback`).
The fallback refuses non-http(s) URLs and local/private IP literals. If both paths
fail, the Firecrawl error is returned with a `fallback_error` field.
