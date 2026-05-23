# Edge Cases & Mitigation Strategy: Groww Weekly Pulse

This document outlines realistic edge cases that could occur during the automated execution of the Weekly Pulse pipeline. It defines how the system is expected to behave under these conditions and the fallback strategies in place.

---

## 1. Over-Aggressive Deterministic Pruning
*   **Scenario:** The regex-based PII scrubber misidentifies valid context as PII and strips it out.
*   **When it occurs:** Phase 1 (Ingestion). For example, a user writes, "I keep getting Error Code 9876543210 on the payment screen," and the regex strips the number because it matches the pattern of a 10-digit phone number.
*   **Impact:** Loss of specific technical context for product teams.
*   **Expected System Behavior:** The regex replaces the text with a generic `<REDACTED_NUM>` tag rather than deleting the sentence entirely.
*   **Mitigation or Fallback Strategy:** Because we use semantic embeddings (`BAAI/bge-small-en-v1.5`), the model still understands the surrounding context ("payment screen", "Error Code"). The review will still be accurately clustered into the "Payments" theme, even without the specific error ID.

## 2. No Dense Clusters Found (Low Issue Concentration)
*   **Scenario:** HDBSCAN fails to find 5 distinct clusters, categorizing the vast majority of reviews as "noise".
*   **When it occurs:** Phase 2 (Clustering). This happens during a "quiet" week where user feedback is highly scattered across dozens of minor, unrelated bugs, with no single overwhelming issue.
*   **Impact:** The system cannot extract 100 representative reviews across 5 themes.
*   **Expected System Behavior:** The clustering algorithm successfully identifies only 2 or 3 valid clusters.
*   **Mitigation or Fallback Strategy:** The Python orchestrator dynamically catches the cluster count. If clusters < 3, it slightly loosens the HDBSCAN `min_cluster_size` and retries once. If it still cannot find 5 themes, it gracefully degrades: the final pulse note is generated with only the found themes (e.g., 2 themes), and the LLM explicitly notes, *"Issue concentration is exceptionally low this week; feedback is highly fragmented."*

## 3. Disguised Contextual PII in Extracted Quotes
*   **Scenario:** A user writes PII in a non-standard way that defeats regex (e.g., "my pan card is abcde one two three four f" or "call me at nine eight seven...").
*   **When it occurs:** Phase 3 (LLM Synthesis). The review survives Phase 1, gets clustered, and the LLM selects it as one of the top 3 quotes to publish.
*   **Impact:** Severe privacy breach if the raw quote is sent to the internal alias.
*   **Expected System Behavior:** The Phase 3 Deep PII Validation LLM pass catches the contextual PII.
*   **Mitigation or Fallback Strategy:** If the validation LLM flags the quote, the Orchestrator rejects the quote entirely (rather than attempting to edit it). It then prompts the Synthesis LLM to "Select an alternative quote for Theme X from the 100-review sample."

## 4. LLM Token Limit Exceeded (Rate Limiting)
*   **Scenario:** The prompt exceeds the Groq 12K Tokens Per Minute (TPM) limit or 30 Requests Per Minute (RPM) limit.
*   **When it occurs:** Phase 3 (LLM Synthesis). This usually happens if the 100 sampled reviews are uncharacteristically long (e.g., 100 highly detailed paragraphs instead of standard short reviews).
*   **Impact:** The Groq API returns a `429 Too Many Requests` or `400 Token Limit Exceeded` error, crashing the pipeline.
*   **Expected System Behavior:** The Python script intercepts the API error before crashing.
*   **Mitigation or Fallback Strategy:** 
    *   *For RPM limits:* The system uses the `tenacity` library to apply an exponential backoff sleep, then retries.
    *   *For TPM limits:* If a token limit error is caught, the Orchestrator automatically truncates the sample size (e.g., drops the bottom 25 reviews from the cluster sample) and retries the prompt with a smaller payload.

## 5. MCP Gateway Unavailability (Delivery Failure)
*   **Scenario:** The Google Workspace MCP server is down, or the OAuth credentials/tokens have expired inside the GitHub Actions runner.
*   **When it occurs:** Phase 4 (Output Integration). The pulse note markdown is fully generated, but the system cannot connect to Gmail or Google Docs.
*   **Impact:** The note is not drafted in the expected inbox.
*   **Expected System Behavior:** The Python script throws a connection/authentication exception.
*   **Mitigation or Fallback Strategy:** The Orchestrator catches the MCP error and immediately dumps the generated markdown note as a raw text artifact into the GitHub Actions run logs. This ensures the 10 minutes of compute and the final insights are not lost. It then causes the GitHub Action to fail, triggering a standard CI/CD failure alert to the technical owner.
