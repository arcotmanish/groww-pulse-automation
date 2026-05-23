# Expert Reasoning Frameworks: Groww Weekly Pulse

Based on the problem statement for the Groww App Automated Weekly Review Pulse, solving this effectively requires looking at the problem through four distinct expert reasoning frameworks. These frameworks focus on how to interpret, process, and deliver the solution without touching on specific architecture or tech stacks.

---

## 1. Information Extraction & Semantic Clustering Framework

This framework is about making sense of chaos. It focuses on turning unstructured, varied, and often noisy user reviews into structured, reliable business signals.

*   **How the expert thinks:** Looks at raw text as a landscape of user intent. They focus on separating "signal" (actual user pain points) from "noise" (spam, generic rants). They think in terms of semantic similarity and categorization, always mapping text back to core business domains (e.g., KYC, withdrawals).
*   **Key Objectives:** Accurately group hundreds or thousands of reviews into a maximum of 5 meaningful, distinct themes. Extract the most representative quotes that capture the essence of each theme.
*   **Key Risks:** Over-generalization (creating useless themes like "App Issues"); misinterpretation of sarcasm or vernacular; missing a critical but low-volume emerging issue because it gets drowned out by existing noise.
*   **Key Tradeoffs:** **Dynamic vs. Static Clustering.** Allowing the system to dynamically generate new themes catches emerging issues, but mapping to strict, static business domains makes week-over-week tracking easier.
*   **Key Decision Criteria:** Do the generated themes directly map to areas owned by internal Groww product squads? Are the themes distinct enough from one another?

## 2. Cognitive Load & Executive Summarization Framework

This framework focuses on the human element of the solution—how the final output is consumed by busy stakeholders (Leadership, Product, Support).

*   **How the expert thinks:** Values the reader's time above all else. They view every unnecessary word as a cognitive tax. They think in terms of information density, scannability, and provoking action rather than just reporting facts.
*   **Key Objectives:** Condense complex, varied user feedback into a highly readable, ≤250-word note. Formulate exactly 3 concrete, realistic action ideas that product teams can immediately assess.
*   **Key Risks:** Over-summarizing to the point where the severity of user pain is diluted; generating generic, unactionable recommendations (e.g., "Improve KYC process") that get ignored.
*   **Key Tradeoffs:** **Comprehensiveness vs. Impact.** Choosing to omit the 4th or 5th most common issue entirely in order to ensure the top 3 issues are highlighted with enough depth and clarity.
*   **Key Decision Criteria:** Strict adherence to the 250-word limit. The visual scannability of the output (use of bullets, bolding). The concreteness and feasibility of the action ideas.

## 3. Data Privacy & Compliance Framework

This framework applies a "zero trust" mindset to user-generated content, ensuring the organization is protected from data exposure.

*   **How the expert thinks:** Assumes all unstructured text is a potential liability. They anticipate edge cases where users might unexpectedly share sensitive information (e.g., typing their PAN number or email in a frustration-fueled review).
*   **Key Objectives:** Guarantee strictly zero Personally Identifiable Information (PII) — no names, emails, or user IDs — in the final pulse note or any synthesized output.
*   **Key Risks:** Users obfuscating PII (e.g., "my email is john dot doe at gmail"), which standard filters might miss; accidentally exposing financial context linked to a specific identifiable user.
*   **Key Tradeoffs:** **Aggressive vs. Lenient Redaction.** Aggressive redaction might remove too much context and render a user quote unreadable, while lenient redaction risks a compliance breach.
*   **Key Decision Criteria:** Failsafe reliability of the PII stripping mechanism. A zero-tolerance policy for leaks in the drafted email.

## 4. Systems Engineering & Automation Framework

This framework views the problem as a continuous, hands-off pipeline. It focuses on the reliability and predictability of the workflow.

*   **How the expert thinks:** Thinks in terms of state, triggers, fault tolerance, and hand-offs. They want a "set it and forget it" system where the only human interaction is reading the final email.
*   **Key Objectives:** Achieve a zero-manual-effort flow from raw data ingestion to the final email draft sitting in the correct inbox on a reliable weekly cadence.
*   **Key Risks:** Silent failures (the pipeline breaks but no one is notified); upstream data format changes from the App/Play Store breaking the ingestion; generating duplicate emails.
*   **Key Tradeoffs:** **Robustness vs. Complexity.** Building highly complex error handling and retry mechanisms ensures delivery but makes the system harder to maintain and audit.
*   **Key Decision Criteria:** Idempotency (can it be re-run safely without sending two emails?). The reliability of the scheduling mechanism. The ease with which the internal team can forward the final drafted artifact.
