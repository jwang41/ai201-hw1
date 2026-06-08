# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

This project covers home finance investment knowledge for families, including household investment strategy, tax-aware account selection, insurance planning, debt management, estate and gifting strategy, and retirement withdrawal planning. This knowledge is valuable because it helps households make better investment and savings decisions over the long term, and it is hard to find through official channels because investment guidance is often scattered across tax rules, insurance sales materials, retirement plan summaries, and general financial advice rather than being integrated into a family-focused home finance investment context.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | 现金流预算 | Practical guidance for household budgeting and expense planning. | `hw1/raw_material/家庭财务基础/现金流预算.md` |
| 2 | 净资产追踪 | Methods for tracking assets, liabilities, and long-term net worth growth. | `hw1/raw_material/家庭财务基础/净资产追踪.md` |
| 3 | 紧急基金 | Frameworks for sizing and maintaining a household emergency reserve. | `hw1/raw_material/家庭财务基础/紧急基金.md` |
| 4 | 保险规划总纲 | Overview of insurance categories and how they protect family financial goals. | `hw1/raw_material/家庭财务基础/保险规划总纲.md` |
| 5 | 债务管理 | Strategies for prioritizing debt repayment and reducing borrowing costs. | `hw1/raw_material/补充-家庭财务/债务管理.md` |
| 6 | 教育规划与风险管理 | Planning for education costs and balancing savings with insurance risk controls. | `hw1/raw_material/补充-家庭财务/教育规划与风险管理.md` |
| 7 | 应税账户基础 | Foundations of taxable investment accounts and when to use them. | `hw1/raw_material/补充-账户提取赠与/应税账户基础.md` |
| 8 | 遗产赠与税-提取策略 | Estate, gifting, and account withdrawal strategies for household transfer planning. | `hw1/raw_material/补充-账户提取赠与/遗产赠与税-提取策略.md` |
| 9 | 4%规则与安全提取率 | Retirement withdrawal rules for sustainable household spending after retirement. | `hw1/raw_material/退休规划/4%规则与安全提取率.md` |
| 10 | Backdoor-Roth-IRA | Tax-aware retirement account planning and Roth conversion strategy. | `hw1/raw_material/退休账户/Backdoor-Roth-IRA.md` |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
