# Groww Weekly Pulse - Implementation Plan

## Phase 1: Automated Ingestion & Deterministic Pruning

- **Objective**: Establish a robust data pipeline that automatically scrapes live reviews from the Play Store and App Store, then outputs a highly sanitized, deduped, and compressed dataset.
- **Ordered Tasks**:
  1. Set up the Python project structure and dependency management (Pandas, Regex tools, `google-play-scraper`, `app-store-scraper`).
  2. Implement Play Store scraper for "com.nextbillion.groww" to fetch reviews from the last 8-12 weeks.
  3. Implement App Store scraper for the iOS "Groww Stocks, Mutual Fund IPO App" to fetch recent reviews.
  4. Standardize the data from both stores into a unified format.
  5. Implement the regex-based PII scrubber (emails, phone numbers, PAN, etc.).
  6. Implement data pruning rules (drop < 4 words, deduplicate exact matches, filter non-English).
- **Explicit Non-Goals**: Do NOT implement any ML embeddings, LLM calls, or database storage in this phase.
- **Definition of Done**: A script connects to both stores, pulls the latest reviews, merges them, and outputs a cleaned CSV containing only high-value, regex-scrubbed reviews, significantly reducing the row count from the scraped volume.
- **Non-Technical Verification Step**: The product owner can open the final CSV file in Excel. They will visually confirm it contains recent reviews from both iOS and Android, has no obvious phone numbers or emails, and contains no single-word reviews like "good".
- **Dependencies or Risks**: 
  - Risk: App stores change their frontend structure, causing the unofficial scraping libraries to break.
  - Risk: Over-aggressive regex might strip valid context (e.g., mistaking a product ID for a phone number).
- **Input to next phase**: The outputted clean, pruned CSV file containing merged App Store and Play Store reviews.

Stop here. Do not proceed to the next phase. Wait for confirmation before continuing.

---

## Phase 2: Local Vector Embeddings & Clustering (ChromaDB)

- **Objective**: Convert the pruned text into semantic clusters to identify the top themes purely mathematically, avoiding LLM token bloat and rate limits.
- **Ordered Tasks**:
  1. Integrate `sentence-transformers` and the `BAAI/bge-small-en-v1.5` model.
  2. Set up ChromaDB `EphemeralClient` to ingest the pruned reviews.
  3. Generate embeddings for the pruned reviews and store them in ChromaDB.
  4. Implement HDBSCAN over the embeddings to cluster the reviews.
  5. Extract the top 5 largest clusters and sample the 20 most central reviews per cluster (100 total).
- **Explicit Non-Goals**: Do NOT name the clusters (themes) yet. Do NOT summarize or extract quotes. Do NOT call the Groq API.
- **Definition of Done**: A script takes the clean CSV, runs it through the local BGE model, clusters it, and outputs exactly 5 groups of 20 reviews each in a JSON structure.
- **Non-Technical Verification Step**: The product owner is presented with a text file containing 5 un-named groups of 20 reviews. By reading through a group, they should intuitively see that all 20 reviews in that group are talking about the exact same pain point (e.g., all complaining about a KYC bug), proving the semantic clustering works mathematically.
- **Dependencies or Risks**: 
  - Risk: HDBSCAN tuning parameters might categorize too much data as "noise" or lump distinct issues into one massive cluster.
- **Input to next phase**: A JSON file containing the top 5 clusters with 20 representative reviews each (exactly 100 reviews).

Stop here. Do not proceed to the next phase. Wait for confirmation before continuing.

---

## Phase 3: LLM Synthesis & Deep PII Validation (Groq)

- **Objective**: Use Groq (`llama-3.3-70b-versatile`) to read the 100 representative reviews, generate the final 250-word pulse note, and guarantee zero contextual PII leakage.
- **Ordered Tasks**:
  1. Integrate the Groq API with robust `tenacity` retry logic (respecting 30 RPM limits).
  2. Write the Synthesis prompt: pass the 5 JSON clusters and ask the LLM to identify the top 3 themes, extract 3 quotes, and generate 3 actions.
  3. Write the Deep PII prompt: pass only the 3 extracted quotes and ask the LLM to verify or redact contextual PII (e.g., "my pan is abcde").
  4. Implement a deterministic word count check (< 250 words) on the final text.
- **Explicit Non-Goals**: Do NOT send the output anywhere (no emails, no Google Docs). Do NOT use any LLM other than Groq.
- **Definition of Done**: The script takes the clustered JSON and reliably generates a final, formatted markdown string that is <250 words, has 3 themes/quotes/actions, and passes the strict PII check, without hitting Groq rate limits.
- **Non-Technical Verification Step**: The product owner reads the final generated markdown text on their screen. They can verify it takes under 2 minutes to read, directly addresses real issues, contains 3 realistic action items, and has zero PII in the quotes.
- **Dependencies or Risks**: 
  - Risk: The LLM hallucinates fake quotes or generates action items that are too vague/generic.
- **Input to next phase**: The finalized markdown text of the Weekly Pulse note.

Stop here. Do not proceed to the next phase. Wait for confirmation before continuing.

---

## Phase 4: Output Integration (MCP)

- **Objective**: Automate the delivery of the note via MCP (Gmail/Docs).
- **Ordered Tasks**:
  1. Integrate the Python MCP SDK.
  2. Configure the Google Workspace MCP servers (Docs & Gmail).
  3. Write the integration code to create a Google Doc from the markdown text and draft an email linking to it.
- **Explicit Non-Goals**: Do NOT build a custom UI or dashboard. Do NOT auto-send the email (it must strictly be drafted).
- **Definition of Done**: The script successfully uses MCP to create a Google Doc with the pulse note and draft an email with the link in the designated Gmail inbox.
- **Non-Technical Verification Step**: The product owner runs the script manually, logs into their designated Gmail account, and sees a "Draft" email containing the formatted pulse note and a working link to a newly created Google Doc.
- **Dependencies or Risks**: 
  - Risk: MCP server connection or OAuth scope issues.
- **Input to next phase**: The completed script that can generate the markdown and output it via MCP.

Stop here. Do not proceed to the next phase. Wait for confirmation before continuing.

---

## Phase 5: Orchestration (GitHub Actions)

- **Objective**: Schedule the entire pipeline on a zero-touch weekly cron.
- **Ordered Tasks**:
  1. Port the entire pipeline into a GitHub Actions `.yml` workflow with cron scheduling and Secrets management.
- **Explicit Non-Goals**: Do NOT build any new application logic, only orchestration.
- **Definition of Done**: The GitHub Action runs successfully on a schedule, executing phases 1-4, and successfully results in a new drafted email in a designated Gmail inbox and a new Google Doc.
- **Non-Technical Verification Step**: The product owner logs into their designated Gmail account on Monday morning and sees a "Draft" email containing the formatted pulse note and a working link to a newly created Google Doc generated by the automated runner.
- **Dependencies or Risks**: 
  - Risk: MCP server connection or OAuth scope issues inside the headless GitHub Actions runner environment.
- **Input to next phase**: N/A (Project Complete).

Stop here. Do not proceed to the next phase. Wait for confirmation before continuing.

---

## Risk Analysis

### Highest-Risk Layer
The **Phase 2: Local Vector Embeddings & Clustering** layer remains the highest technical risk. If HDBSCAN fails to properly tune out noise, the LLM in Phase 3 will receive garbage. However, **Phase 1 Automated Scraping** introduces a new operational risk: unnotified structural changes to the Play Store or App Store web frontends could break the scraping libraries without warning.

### How the Plan Reduces Risk Progressively
1. **Phase 1 mitigates data volume and ingestion risks** by automating the scraping and aggressively pruning garbage deterministically. 
2. **Phase 2 mitigates LLM rate-limit and cost risks** by completely avoiding LLMs for the heavy lifting of sorting thousands of reviews. 
3. **Phase 3 mitigates hallucination and privacy risks** by working *only* with the highly concentrated 100 reviews produced by Phase 2.
4. **Phase 4 mitigates output risks** by testing the Google Workspace MCP integration locally first.
5. **Phase 5 mitigates operational risk** by waiting until the core logic and outputs are proven (Phases 1-4) before introducing the complexities of CI/CD runners and Secrets management.
