# Architectural & Implementation Decisions

## 1. Automated Live Scraping vs. Static CSVs
**Decision:** Implemented `scraper.py` which fetches live reviews from publicly accessible App Store and Play Store endpoints using lightweight scraping libraries.
**Rationale:** The original problem statement mentioned using "exported" reviews. However, to achieve a true "zero-touch" weekly automated pipeline (Phase 4), we shifted to using `google-play-scraper` and `app-store-scraper`. This removes the need for any human to manually export and upload CSVs every week.

## 2. Semantic Quality Filtering (Deterministic)
**Decision:** Added a deterministic semantic filter layer in Phase 1 before vector embeddings. It uses sets of "signal keywords" (like bug, charge, feature) and drops reviews that only contain generic praise (like "good app", "very nice") combined with common stop words.
**Rationale:** HDBSCAN and embedding models treat all input equally. Generic praise clusters heavily due to lexical similarity, which drowns out low-volume but high-importance bug reports or feature requests. By explicitly hard-filtering generic praise at the ingestion layer using fast Python sets, we dramatically improve the signal-to-noise ratio of the clusters without burning LLM tokens or API latency on noise.
