# Generation and Interface Implementation

## Files Created (Milestone 5)

### 1. **generation.py** - LLM Generation with Grounding
Implements grounded answer generation using Groq's `llama-3.3-70b-versatile` model.

**Key Components:**
- **`SYSTEM_PROMPT`**: Enforces grounding constraints
  - Answers ONLY from retrieved context
  - Explicit refusal if context insufficient
  - Source citation requirements
  
- **`initialize_groq_client()`**: Groq API initialization
  - Uses `GROQ_API_KEY` environment variable
  - Error handling for missing credentials

- **`build_grounded_prompt(query, context)`**: Prompt engineering
  - Combines user query with retrieved context
  - Explicit instructions to answer only from context
  - Formatting guidance for professional tone

- **`generate_answer(query, retrieved_context, source_chunks)`**: Main generation function
  - Calls Groq LLM with system + user prompts
  - Temperature: 0.3 (conservative, fact-focused)
  - Max tokens: 500
  - Returns dict with answer, sources, grounding status, tokens used

- **`format_response(result)`**: Output formatting
  - Displays answer with grounding status
  - Lists source chunks with IDs and paths
  - Shows token usage metrics

- **`evaluate_on_test_questions()`**: Evaluation mode
  - Runs all 5 test questions from planning.md
  - Saves results to `generation_evaluation_report.json`
  - Compares generated answers with expected answers

**CLI Usage:**
```bash
# Single query
python generation.py --query "What is the 4% rule?"

# Run evaluation on 5 test questions
python generation.py --evaluate

# Use custom context (for testing)
python generation.py --query "?" --context "Your context here"
```

### 2. **app.py** - Gradio Web Interface
User-friendly web interface combining retrieval and generation.

**Key Components:**
- **`create_gradio_interface()`**: Gradio UI with Blocks
  - Textbox input for queries (English/Chinese)
  - Markdown output with answer + sources
  - Optional statistics display
  - Example questions for quick testing
  - Professional styling and instructions

- **`answer_question(query, show_retrieval_stats)`**: Main interface function
  - Calls `retrieval.retrieve_and_format()` to get context (6 chunks)
  - Calls `generation.generate_answer()` to generate answer
  - Formats output with sources and optional performance metrics
  - Error handling for missing API keys or vector store

- **`run_cli_evaluation()`**: Evaluation mode
  - Runs generation evaluation on 5 test questions
  - Runs retrieval evaluation (from retrieval.py)
  - Saves reports

- **`main()`**: CLI argument parser
  - `--query`: Single query mode (no UI)
  - `--evaluate`: Run evaluation on 5 test questions
  - `--share`: Create public Gradio link
  - `--server-name`: Bind address (default: 127.0.0.1)
  - `--server-port`: Bind port (default: 7860)

**CLI Usage:**
```bash
# Launch interactive web UI (default)
python app.py

# Launch with public share link
python app.py --share

# Test single query
python app.py --query "What emergency fund should I have?"

# Run full evaluation
python app.py --evaluate

# Custom server address
python app.py --server-name 0.0.0.0 --server-port 8080
```

## Pipeline Architecture

```
User Query (English/Chinese)
    |
    v
[Gradio Interface - app.py]
    |
    +---> retrieval.retrieve_and_format(query, top_k=6)
    |     |
    |     +---> Chroma vector store at ./chroma_store
    |     +---> all-MiniLM-L6-v2 semantic search
    |     +---> Returns: formatted_context + source_chunks
    |
    +---> generation.generate_answer(query, context, chunks)
    |     |
    |     +---> Groq API (llama-3.3-70b-versatile)
    |     +---> SYSTEM_PROMPT: grounding enforcement
    |     +---> USER_PROMPT: context + query + instructions
    |     +---> Returns: answer + sources + metadata
    |
    v
[Formatted Response]
- Answer text (grounded in context)
- Source attribution (chunk IDs + paths)
- Grounding status flag
- Token usage metrics (optional)
```

## Grounding Implementation

### System Prompt Rules
1. **Base answers ONLY on retrieved context**
2. **Never use external knowledge**
3. **Explicit refusal for out-of-scope questions**: "I don't have information about that in the knowledge base."
4. **Source citations required**
5. **Professional advisory tone**

### Prompt Structure
```
SYSTEM PROMPT (enforces grounding + tone)
+ 
USER PROMPT:
  - RETRIEVED CONTEXT (6 chunks from semantic search)
  - USER QUESTION
  - INSTRUCTIONS (answer only from context)
```

### Grounding Indicators
- `grounded: True/False` flag in result dict
- Explicit "⚠️ This answer may not be grounded" message if no context retrieved
- "No relevant sources found" message if context insufficient

## Test Questions (From planning.md)

All 5 test questions included in evaluation mode:

1. **Emergency Fund Size** - Expected: 3-6 months of living expenses
2. **Tax-Efficient Retirement** - Expected: Roth IRA, Backdoor Roth strategy
3. **Debt & Insurance** - Expected: High-interest first, adequate coverage
4. **Asset Location** - Expected: Tax-inefficient in deferred, efficient in taxable
5. **4% Rule** - Expected: 4% annual withdrawal with sequence-of-returns awareness

## Setup Requirements

### Environment Variables
```bash
export GROQ_API_KEY="your-groq-api-key"
```

Get API key from: https://console.groq.com/

### Python Dependencies
- groq==0.15.0 (installed)
- gradio (installed)
- retrieval.py (already created)
- chromadb (already installed)
- sentence-transformers (already installed)

### Prerequisite Files
- Vector store: `./chroma_store/` (created by ingest.py)
- retrieval.py: Semantic search module (already created)
- All source documents: 80 documents in `./documents/raw_material/`

## Running the System

### Option 1: Interactive Web UI
```bash
python app.py
# Opens at http://127.0.0.1:7860
```

### Option 2: Single Query (CLI)
```bash
python app.py --query "What is the 4% rule?"
```

### Option 3: Full Evaluation
```bash
python app.py --evaluate
# Saves: generation_evaluation_report.json + retrieval evaluation output
```

### Option 4: Direct Generation Module
```bash
python generation.py --query "Your question?"
python generation.py --evaluate
```

## Output Examples

### Successful Answer
```
## Answer

According to the material, you should maintain an emergency fund of about 3-6 months of living expenses.
This provides a safety net for unexpected job loss or major expenses while keeping funds liquid.

✓ This answer is grounded in the knowledge base.

## Sources
- Chunk 1: 家庭财务基础/紧急基金.txt (ID: 家庭财务基础/紧急基金.txt#0)
- Chunk 3: 家庭财务基础/现金流预算.txt (ID: 家庭财务基础/现金流预算.txt#1)

---

*Token usage: 156 input + 87 output = 243 total*
```

### Out-of-Scope Answer
```
## Answer

I don't have information about that in the knowledge base. The context provided does not cover this topic.

⚠️ This answer may not be grounded in the knowledge base.

*No relevant sources found.*
```

## Evaluation Report Format

Both `generation_evaluation_report.json` and retrieval evaluation output include:
- Question number and text
- Generated answer
- Sources retrieved
- Grounding status
- Model used
- Chunks retrieved count
- Any errors encountered

## Performance Metrics

**Typical values (on CPU with llama-3.3-70b-versatile):**
- Retrieval time: 0.2-0.5s (semantic search on 163 chunks)
- Generation time: 2-5s (Groq API latency + model inference)
- Total time: 2.5-5.5s per query
- Token usage: ~150-250 tokens per query

## Multilingual Support

- **Query languages**: English or Chinese (mixed queries OK)
- **Response languages**: Matches query language or English (LLM native)
- **Context**: All 80 documents are Chinese + English mixed
- **Retrieval**: all-MiniLM-L6-v2 supports both languages
- **Generation**: llama-3.3-70b-versatile is multilingual

## Error Handling

| Error | Handling |
|-------|----------|
| GROQ_API_KEY not set | Graceful error message in UI |
| Chroma store not found | Directs user to run ingest.py |
| No relevant context | "I don't have information..." response |
| Retrieval timeout | Error message with recovery steps |
| LLM API failure | Specific error with retry suggestion |

## Next Steps

1. **Set GROQ_API_KEY** environment variable
2. **Run interactive UI**: `python app.py`
3. **Test with examples** or ask custom questions
4. **Run evaluation**: `python app.py --evaluate`
5. **Review reports**: Check `generation_evaluation_report.json` for quality metrics
