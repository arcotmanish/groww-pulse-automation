# Recommended Tech Stack: Groww Weekly Pulse

Based on the token-optimized architecture defined in `Architecture.md` and specific operational constraints, the following tech stack will be used. This stack is strictly optimized to operate within tight LLM rate limits while maintaining high performance.

---

## 1. Core Orchestration & Application Logic: Python 3.11+
*   **Why it fits:** Python is the undisputed leader for data pipelines, ML/vector clustering, and LLM orchestration. It provides mature libraries for every module required in the architecture (Pandas for pruning, Scikit-Learn for clustering, LangChain/MCP SDKs for orchestration).
*   **Tradeoffs:** Slower execution speed compared to compiled languages (Go/Rust), and dynamic typing can lead to runtime errors if not rigorously checked.
*   **Scaling implications:** Memory consumption is higher than Node.js, but standard CI/CD runners can easily handle in-memory processing of 100k rows.
*   **Operational complexity:** Low. Standard virtual environments and `requirements.txt`.
*   **Alternatives considered:** Node.js (weaker data science ecosystem for the vector clustering phase).

## 2. Ingestion & Data Processing: Python Scrapers + Pandas + Regex
*   **Why it fits:** 
    *   **Scrapers:** `google-play-scraper` and `app-store-scraper` provide highly reliable, zero-auth programmatic access to live app store reviews, removing the need for manual CSV exports.
    *   **Pandas & Regex:** Allows for hyper-fast, vectorized operations to drop short reviews, remove duplicates, and run regex for PII scrubbing across thousands of scraped rows in milliseconds. This is critical to reduce the dataset before it hits the LLM.
*   **Tradeoffs:** Unofficial scrapers can break if Apple or Google changes their web frontend. Pandas processes data entirely in-memory. 
*   **Scaling implications:** 8–12 weeks of reviews is easily handled in-memory (taking only a few dozen megabytes). 
*   **Operational complexity:** Low. Requires adding the scraper libraries to `requirements.txt` and handling potential rate limits from the app stores during the initial fetch.
*   **Alternatives considered:** Manual CSV exports (rejected to achieve true zero-touch automation), commercial scraping APIs (adds unnecessary cost).

## 3. Vector Embeddings & Clustering: `BAAI/bge-small-en-v1.5` + ChromaDB + HDBSCAN
*   **Why it fits:** 
    *   **Embedding Model:** `BAAI/bge-small-en-v1.5`. This is currently one of the top-performing small, open-source embedding models on the MTEB leaderboard. It produces highly accurate semantic vectors (384 dimensions) while remaining small enough to run efficiently on CPU within a GitHub Actions runner.
    *   **Vector DB:** **ChromaDB** is a lightweight, developer-friendly database that can run completely in-memory (`EphemeralClient`) during the weekly batch job without requiring a dedicated server. By passing `BAAI/bge-small-en-v1.5` via the HuggingFace embedding function, Chroma handles it seamlessly.
    *   **Clustering:** Combined with **HDBSCAN**, it perfectly groups semantically similar embedded reviews into dense clusters while discarding noisy, irrelevant reviews.
*   **Tradeoffs:** Requires explicitly loading the HuggingFace model in ChromaDB, pulling a slightly larger model than the default MiniLM, but the quality trade-off is well worth it.
*   **Scaling implications:** CPU-based embedding for 100k reviews will take a few minutes in a GitHub Action, but completely avoids any external API rate limits or costs. 
*   **Operational complexity:** Low. Requires adding `sentence-transformers` and pointing the Chroma embedding function to the `BAAI/bge-small-en-v1.5` Hugging Face repo.
*   **Alternatives considered:** `all-MiniLM-L6-v2` (Chroma default, slightly faster but noticeably lower quality than BGE).

## 4. LLM Synthesis Engine: Groq (`llama-3.3-70b-versatile`)
*   **Why it fits:** Groq provides blisteringly fast inference for open-source models. `llama-3.3-70b-versatile` is highly capable of advanced reasoning, strict JSON formatting, and PII detection.
*   **Tradeoffs & Constraints:** Strict rate limits apply: **30 Requests Per Minute (RPM), 12K Tokens Per Minute (TPM), and 100K Tokens Per Day (TPD)**. 
*   **Scaling implications:** The 12K TPM limit *mandates* our funnel architecture. We absolutely cannot send raw reviews to the LLM. By using ChromaDB to sample exactly 100 representative reviews, our prompt will be around ~3K-5K tokens, comfortably fitting inside the 12K TPM limit. We must batch our prompts (e.g., 1 prompt for synthesis, 1 prompt for PII checking) to stay well under the 30 RPM limit.
*   **Operational complexity:** Medium. Requires rigorous implementation of `tenacity` (retry with exponential backoff) and token counting before making requests to avoid hitting rate limit exceptions.
*   **Alternatives considered:** OpenAI GPT-4o-mini (rejected in favor of high-speed open-source inference via Groq).

## 5. Infrastructure & Triggering: GitHub Actions
*   **Why it fits:** A weekly automated pulse note is perfectly suited for GitHub Actions cron scheduling (`schedule: - cron: '0 8 * * 1'`). It provides free compute for public repos (and generous minutes for private), native secrets management for the Groq API key and MCP credentials, and excellent execution logs.
*   **Tradeoffs:** GitHub Actions standard runners have a 6-hour timeout (plenty of time for this) but limited RAM (~7GB).
*   **Scaling implications:** 7GB RAM is more than enough to load ChromaDB, Pandas, and the 100k review dataset in memory.
*   **Operational complexity:** Low. Requires a single `.yml` workflow file and GitHub Secrets setup.
*   **Alternatives considered:** AWS Lambda (15-minute timeout might be risky if clustering takes long), GCP Cloud Run.

## 6. Integrations: Model Context Protocol (MCP) Python SDK
*   **Why it fits:** The architecture requires MCP integration for Google Docs and Gmail. The official Python MCP SDK allows the Orchestrator to securely connect to external MCP servers to execute tool calls.
*   **Tradeoffs:** MCP is an emerging standard; debugging can be more complex than standard REST APIs.
*   **Scaling implications:** Bounded by Google Workspace API rate limits, which are extremely generous for a weekly run.
*   **Operational complexity:** Medium. Requires hosting the Gmail/Docs MCP servers locally within the GitHub Actions runner or connecting to a remote MCP host.
*   **Alternatives considered:** Direct Google API Client libraries (violates the architectural requirement to use MCP).
