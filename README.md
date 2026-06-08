# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This project focuses on home finance investment for families, including household investment strategy, tax-aware account selection, insurance planning, debt management, estate planning, and retirement withdrawal strategy. The knowledge is hard to find through official channels because investment-related guidance is often fragmented across insurance providers, tax code summaries, retirement plan guides, and marketing materials instead of being integrated into a holistic family investment and home finance playbook.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | 现金流预算 | Home finance budgeting guide | `hw1/raw_material/家庭财务基础/现金流预算.md` |
| 2 | 净资产追踪 | Net worth tracking for household finance | `hw1/raw_material/家庭财务基础/净资产追踪.md` |
| 3 | 紧急基金 | Emergency fund planning for families | `hw1/raw_material/家庭财务基础/紧急基金.md` |
| 4 | 保险规划总纲 | Insurance planning overview | `hw1/raw_material/家庭财务基础/保险规划总纲.md` |
| 5 | 债务管理 | Debt repayment and credit management | `hw1/raw_material/补充-家庭财务/债务管理.md` |
| 6 | 教育规划与风险管理 | Education savings and risk management | `hw1/raw_material/补充-家庭财务/教育规划与风险管理.md` |
| 7 | 应税账户基础 | Taxable investment account fundamentals | `hw1/raw_material/补充-账户提取赠与/应税账户基础.md` |
| 8 | 遗产赠与税-提取策略 | Estate, gifting, and withdrawal strategy | `hw1/raw_material/补充-账户提取赠与/遗产赠与税-提取策略.md` |
| 9 | 4%规则与安全提取率 | Sustainable retirement withdrawal rules | `hw1/raw_material/退休规划/4%规则与安全提取率.md` |
| 10 | Backdoor-Roth-IRA | Roth IRA conversion and tax-efficient retirement planning | `hw1/raw_material/退休账户/Backdoor-Roth-IRA.md` |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
