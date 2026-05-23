# Problem Statement — Groww App: Automated Weekly Review Pulse

---

## Context & Why This Matters

Groww is a high-growth consumer fintech app serving millions of retail investors. User reviews on the App Store and Play Store are one of the most unfiltered, real-time signals of product health — yet today, these signals sit unread in platform dashboards, processed only when a crisis emerges. Product, Support, and Leadership teams are making decisions without a structured, recurring view of what users are actually experiencing week to week.

The gap is not data — it's synthesis. Reviews exist. What's missing is a reliable, low-effort mechanism to surface the *right* themes, *real* user voices, and *actionable* direction from them on a weekly cadence.

---

## What We're Trying to Solve

We need an automated pipeline that:

- **Ingests** publicly exported App Store and Play Store reviews from the last 8–12 weeks
- **Clusters** them into a maximum of **5 meaningful themes** relevant to Groww's core user journeys (e.g. onboarding, KYC, payments, portfolio statements, withdrawals)
- **Condenses** everything into a scannable, under-250-word **one-page weekly pulse note** containing:
  - Top 3 recurring themes
  - 3 anonymised real user quotes *(no PII — no names, emails, or IDs)*
  - 3 concrete action ideas derived from patterns
- **Auto-drafts an email** with this note and sends it to a designated internal recipient or alias — ready to forward with zero manual effort

---

## Who Benefits & How

| Audience | Benefit |
|---|---|
| **Product & Growth Teams** | Structured "what to fix next" signal every week |
| **Support Teams** | Advance awareness of user pain points for proactive acknowledgement |
| **Leadership** | Lightweight, consistent weekly health indicator — no raw data needed |

---

## Boundaries & Constraints

| Constraint | Detail |
|---|---|
| Data source | Public review exports only — no login-gated scraping |
| Theme cap | Maximum 5 themes per pulse |
| Note length | ≤ 250 words — must be genuinely scannable |
| PII | Strictly zero — no usernames, emails, or user IDs in any output |
| Delivery | Email draft is the final artefact |

---

## The Outcome We're Aiming For

A repeatable, weekly, zero-manual-effort flow:

> **Reviews in → Themes clustered → Pulse note generated → Email drafted and sent**

The team should be able to read the output in under 2 minutes and walk away knowing exactly what users are saying and where to focus next.

---

*This document defines the problem and desired outcome. Implementation approach and tooling decisions are left to the technical team.*
