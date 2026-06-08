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
| 1 | 现金流预算 | Home finance budgeting guide | `./documents/raw_material/家庭财务基础/现金流预算.md` |
| 2 | 净资产追踪 | Net worth tracking for household finance | `./documents/raw_material/家庭财务基础/净资产追踪.md` |
| 3 | 紧急基金 | Emergency fund planning for families | `./documents/raw_material/家庭财务基础/紧急基金.md` |
| 4 | 保险规划总纲 | Insurance planning overview | `./documents/raw_material/家庭财务基础/保险规划总纲.md` |
| 5 | 债务管理 | Debt repayment and credit management | `./documents/raw_material/补充-家庭财务/债务管理.md` |
| 6 | 教育规划与风险管理 | Education savings and risk management | `./documents/raw_material/补充-家庭财务/教育规划与风险管理.md` |
| 7 | 应税账户基础 | Taxable investment account fundamentals | `./documents/raw_material/补充-账户提取赠与/应税账户基础.md` |
| 8 | 遗产赠与税-提取策略 | Estate, gifting, and withdrawal strategy | `./documents/raw_material/补充-账户提取赠与/遗产赠与税-提取策略.md` |
| 9 | 4%规则与安全提取率 | Sustainable retirement withdrawal rules | `./documents/raw_material/退休规划/4%规则与安全提取率.md` |
| 10 | Backdoor-Roth-IRA | Roth IRA conversion and tax-efficient retirement planning | `./documents/raw_material/退休账户/Backdoor-Roth-IRA.md` |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 400 tokens (whitespace-delimited tokens, approximated with `re.findall(r"\S+", text)` rather than a model tokenizer).

**Overlap:** 80 tokens (20% of the chunk size).

**Preprocessing before chunking:** Raw Markdown is loaded from `./documents/raw_material`, then whitespace is normalized (`\r\n`→`\n`, runs of spaces/tabs collapsed, 3+ blank lines reduced to a paragraph break) while paragraph structure is preserved. See `normalize_text()` in [ingest.py](ingest.py#L25). Chunking uses a sliding token window that advances by `chunk_size - overlap` (320 tokens) each step.

**Why these choices fit your documents:** The corpus is 80 short-to-medium household-finance notes (e.g. one file per concept: emergency fund, Backdoor Roth IRA, asset location). A 400-token window is large enough to keep a single concept and its recommendation together, but small enough that a retrieved chunk stays topically focused rather than spanning several unrelated subsections. The 80-token overlap prevents a definition or a numeric rule (e.g. "3–6 months", "4%") from being split across a boundary and lost to retrieval.

**Final chunk count:** 163 chunks across 80 documents, as stored in the live Chroma collection (`home_finance`). (The standalone `chunk_text_strategy.py` run over the separately-cleaned `data/cleaned_text/` set produced 153 chunks; the 163 figure is the count actually queried at retrieval time.)

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (loaded through Chroma's `SentenceTransformerEmbeddingFunction`, running on CPU). It is a compact model (~22M parameters, 384-dimensional embeddings, ~256-token max sequence length) that is fast on CPU and handles the mixed Chinese/English source text well enough for this corpus. Retrieval returns the top **k = 6** chunks per query.

**Production tradeoff reflection:** For a homework-scale corpus this model is the right call — small, free, local, no API latency, and good enough multilingual coverage for the bilingual documents. If I deployed this for real users and cost weren't a constraint, the main tradeoffs I'd weigh:
- **Accuracy on domain-specific text:** A larger or finance/multilingual-tuned model (e.g. `bge-m3`, `text-embedding-3-large`, or a domain-adapted embedding) would better separate close tax/retirement concepts. This corpus already shows the weakness — the English query for Q3 failed to retrieve the Chinese-titled debt-management document (see Failure Case Analysis).
- **Multilingual support:** The documents mix Chinese headers with English finance terms; a model explicitly trained for strong cross-lingual retrieval would reduce the English-query/Chinese-document mismatch.
- **Context length:** `all-MiniLM-L6-v2` truncates at ~256 tokens, shorter than my 400-token chunks, so the tail of each chunk is effectively not embedded. A model with a longer context window (512–8192 tokens) would embed the whole chunk.
- **Latency / hosting:** A local model has zero per-query cost and no network dependency; an API-hosted model adds latency and cost but offloads compute. I'd keep retrieval local unless accuracy gains justified the API.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** Generation uses Groq's `llama-3.3-70b-versatile` at `temperature=0.3`. The grounding is enforced by both a system prompt and the structure of the user prompt (see [generation.py](generation.py)):

- The `SYSTEM_PROMPT` states the model must "answer ONLY on the provided context," must "NOT use external knowledge, assumptions, or information outside the context," and if the context is insufficient must reply verbatim: *"I don't have information about that in the knowledge base. The context provided does not cover this topic."*
- `build_grounded_prompt()` wraps the retrieved chunks in an explicit `RETRIEVED CONTEXT:` block, restates the question, then repeats the instruction to answer only from that block and to say so explicitly when the context doesn't cover the question.
- **Structural guard:** before any LLM call, `generate_answer()` short-circuits when retrieval returned nothing (empty context or `"No relevant documents found."`) and returns the refusal response with `grounded=False`, so the model is never invoked without context.

The grounding visibly works in practice: for the debt/insurance question (Q3) the retrieved context did not include the debt-management document, and the model honestly responded *"there is no specific guidance provided in the given context"* for the debt half rather than inventing it.

**How source attribution is surfaced in the response:** Two complementary mechanisms:
1. **Instructed (inline):** Each chunk is fed to the model with a header `[Chunk N from <source>]`, and the prompt instructs the model to cite the source **document name** when stating a fact (e.g. *"According to Backdoor-Roth-IRA.md, …"*). The generated answers do this — see the Evaluation Report.
2. **Programmatic (guaranteed):** After generation, `_unique_source_names()` collects the de-duplicated document names from the retrieved chunks (in retrieval order) and `generate_answer()` appends a `**Sources:** doc1.md, doc2.md, …` line to the answer. This guarantees attribution even if the model omits an inline citation. The structured result also carries a `source_documents` list and a detailed per-chunk `sources` list rendered under a `## Sources` heading by `format_response()`.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

Run live with `python generation.py --evaluate` (requires `GROQ_API_KEY`). The results below are from an actual run against the `home_finance` Chroma collection (163 chunks), model `llama-3.3-70b-versatile`, top-k = 6. All five answers returned `grounded=True`.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What emergency fund size does the household finance material recommend? | A reserve of about 3–6 months of living expenses. | "According to 紧急基金.md, 3–6 months of necessary expenses," with the right qualifiers (excludes discretionary spend; 3 mo for stable single-income, 6+ mo for unstable/single-income), kept in a liquid high-yield account. Top retrieved chunk: 紧急基金.md (dist 0.42). | Relevant | Accurate |
| 2 | Which account types are tax-efficient for retirement savings, and what is a Backdoor Roth IRA? | Tax-advantaged retirement accounts / Roth for tax-free growth; Backdoor Roth = nondeductible Traditional IRA contribution then converted to Roth when direct Roth is income-limited. | Correctly defines the Backdoor Roth (cites Backdoor-Roth-IRA.md) and adds asset-location guidance (cites Asset-Location.md): tax-efficient equities in taxable, tax-inefficient bonds/REITs in tax-deferred. | Relevant | Accurate |
| 3 | How should families prioritize debt repayment and insurance planning? | High-interest debt first; maintain adequate coverage (term life, health, property/casualty) as financial defense. | Covered insurance from 保险规划总纲.md, but **explicitly stated the context gave no specific debt-repayment guidance**; offered only generic "high-interest first" advice. The dedicated debt doc was not retrieved. | Partially relevant | Partially accurate |
| 4 | What asset-location guidance is given for taxable, tax-deferred, and tax-free accounts? | Tax-inefficient assets (bonds) in tax-deferred; tax-efficient equities in taxable/Roth; highest-growth assets in Roth. | Accurate per Asset-Location.md: tax-inefficient → Traditional 401k/IRA, tax-efficient ETFs (VTI/VOO) → taxable, high-growth → Roth. Top chunk Asset-Location.md (dist 0.33). | Relevant | Accurate |
| 5 | What is the 4% rule and the main caution for retirement withdrawals? | Withdraw ~4% year one, adjust for inflation thereafter; watch sequence-of-returns risk and longevity/inflation. | Correctly describes 4% + inflation adjustment (cites 4%规则与安全提取率.md) and flags depletion risk from poor early-year returns (i.e. sequence-of-returns risk), though it does not name that term explicitly. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

**Summary:** 4 of 5 questions retrieved an on-target top chunk and produced accurate, well-attributed answers. Q3 is the weak case (analyzed below). Note that fixing two pipeline bugs was required before retrieval returned correct sources at all — see Spec Reflection.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q3 — "How should families prioritize debt repayment and insurance planning?"

**What the system returned:** The model answered the insurance half from `保险规划总纲.md`, but for debt repayment it explicitly said *"there is no specific guidance provided in the given context"* and fell back to generic "focus on high-interest debts first" advice rather than grounded content. (This is actually the grounding working correctly — it refused to fabricate.)

**Root cause (tied to a specific pipeline stage):** This is a **retrieval** failure, not a generation one. The corpus *does* contain the answer — `补充-家庭财务/债务管理.md` states the core principle "先消灭坏债 → 再优化好债" (eliminate high-interest "bad debt" first, then optimize "good debt"). But that document never appeared in the top-6. The retrieved chunks for Q3 had notably high distances (0.758–0.800, versus 0.32–0.42 for the questions that worked), and the debt doc was edged out by insurance/Medicare/education chunks. The cause is an **embedding cross-lingual mismatch**: the query is English ("debt repayment"), while `债务管理.md` leads with Chinese headers ("债务管理", "好债 vs 坏债"). `all-MiniLM-L6-v2` only weakly aligns the English query vector with the Chinese-titled chunk, so a semantically central document scored worse than tangential ones. The combined English+Chinese question ("debt repayment **and** insurance") also splits the query vector across two topics, further diluting the debt signal.

**What you would change to fix it:** (1) Swap to a stronger cross-lingual embedding model (e.g. `bge-m3` or `paraphrase-multilingual-MiniLM-L12-v2`) so an English query reliably matches Chinese-titled documents — this is the highest-leverage fix. (2) Normalize chunks so each carries an English-translated title/keywords in its embedded text, giving the English query a lexical anchor. (3) For compound questions, split the query into sub-queries ("debt repayment", "insurance planning") and merge the retrieved sets, so neither topic crowds the other out of the top-6. (4) As a cheap mitigation, raise top-k or add a distance threshold + re-rank so borderline-but-on-topic docs aren't dropped.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Because `planning.md` fixed the concrete numbers up front — 400-token chunks, 80-token overlap, `all-MiniLM-L6-v2`, top-k = 6 — the implementation was almost mechanical to direct. I could hand the Chunking Strategy and Retrieval Approach sections to Claude and get back `chunk_text()` and `retrieve_chunks()` that matched the spec, instead of re-deciding parameters mid-build. Those same numbers became the constants (`CHUNK_SIZE`, `OVERLAP`, `EMBEDDING_MODEL`) at the top of `ingest.py`, keeping the spec and the code in sync. The 5 evaluation questions defined in the spec also doubled as the regression suite I ran in the Evaluation Report.

**One way your implementation diverged from the spec, and why:** `planning.md` never named the Chroma collection or the metadata schema, and the modules drifted apart as a result — `ingest.py` wrote the collection as `home_finance` with metadata key `source_path`, while `retrieval.py` defaulted to a different name (`household_finance`) and read keys `source`/`id`. With the spec silent on these, the mismatch went unnoticed: default retrieval failed to find the collection, and even when pointed at the right one, every source came back as `unknown` — which silently broke source attribution. I diverged from the (under-specified) original code by standardizing both modules on `home_finance` and on reading `source_path` plus Chroma's top-level chunk id, so attribution returns real document names. The lesson is that the spec should have pinned the storage contract (collection name + metadata keys), not just the algorithm parameters.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Implementing the chunker from the spec**

- *What I gave the AI:* The Chunking Strategy section of `planning.md` (400-token chunks, 80-token overlap, reasoning about short finance docs) and asked it to implement `chunk_text()`.
- *What it produced:* A token-window chunker that tokenizes on whitespace (`re.findall(r"\S+", text)`), emits 400-token windows, and advances the start by `chunk_size - overlap`, plus an `id`/`source`/`chunk_index` metadata record per chunk.
- *What I changed or overrode:* I kept the algorithm but tightened preprocessing — text is normalized (`normalize_text()`) to collapse whitespace and cap blank lines before tokenizing, and the chunk id was standardized to `source_path#index` so chunks are traceable to their document.

**Instance 2 — Source attribution and fixing the retrieval bugs**

- *What I gave the AI:* The instruction to make the response name which document(s) each answer came from — either by prompting the model to cite sources or by appending source names programmatically.
- *What it produced:* Updated `SYSTEM_PROMPT`/`build_grounded_prompt()` to cite by document name, plus a `_unique_source_names()` helper and an appended `**Sources:**` line and `source_documents` field in `generate_answer()`.
- *What I changed or overrode:* Testing the attribution surfaced two real bugs the AI's first pass didn't catch: every source rendered as `unknown` because `retrieval.py` read metadata keys (`source`/`id`) that `ingest.py` never wrote (`source_path`), and the default collection name didn't match the stored one. I directed the fix to read `source_path` and Chroma's top-level chunk id and to default to `home_finance`, after which attribution returned correct names (verified in the Evaluation Report).
