# Prompt for Generation and Interface Code (Milestone 5)

## Context

I have built a household finance knowledge retrieval system with these components:
- **Chunking:** 400 tokens per chunk, 80-token overlap (planning.md spec)
- **Embedding:** all-MiniLM-L6-v2 model via sentence-transformers
- **Vector Store:** Chroma at `./chroma_store` with 163 chunks from 80 documents (Chinese + English)
- **Retrieval:** `retrieval.py` module with `retrieve_chunks(query, top_k=6)` and `format_retrieval_context(chunks)`

## Architecture

```
Document Ingestion (80 docs)
         ↓
Chunking (400 tokens, 80 overlap → 163 chunks)
         ↓
Embedding + Vector Store (all-MiniLM-L6-v2 → Chroma)
         ↓
Retrieval (top-6 similarity search with source attribution)
         ↓
Generation (LLM + grounding) ← YOU ARE HERE
         ↓
Interface (Gradio UI)
```

## Task: Generate `generation.py` and `app.py` (Gradio Interface)

### **generation.py Requirements**

1. **System Prompt with Grounding**
   - Enforce that all answers MUST be grounded in retrieved context only
   - If no relevant context retrieved, respond: "I don't have information about that in the knowledge base."
   - Never make up information or use external knowledge
   - Example grounding instruction: "You are a helpful household finance advisor. Base your answer ONLY on the retrieved context provided below. If the context does not answer the question, say 'I don't have information about that.' Do not use external knowledge or make assumptions."

2. **LLM Integration**
   - Use Groq API (client: `groq.Groq()` from groq package in requirements.txt)
   - Model: `mixtral-8x7b-32768` or similar fast model
   - Temperature: 0.3 (conservative, fact-focused)
   - Max tokens: 500

3. **Source Attribution**
   - Each response must include a "Sources" section listing retrieved chunks
   - Format: `[Chunk {N} from {source_path}]`
   - Example output:
     ```
     **Answer:**
     [Your grounded answer here]

     **Sources:**
     - [Chunk 1 from 退休规划/4%规则与安全提取率.txt]
     - [Chunk 3 from 退休账户/Backdoor-Roth-IRA.txt]
     ```

4. **Function Signature**
   ```python
   def generate_answer(query: str, retrieved_context: str, source_chunks: list) -> dict:
       """
       Generate grounded answer using Groq LLM.
       
       Args:
           query: User question (English or Chinese)
           retrieved_context: Formatted context from retrieval.py (from format_retrieval_context)
           source_chunks: Raw chunk list (from retrieve_chunks)
       
       Returns:
           dict with keys: {
               "answer": str (the LLM response),
               "sources": list[str] (formatted source attribution),
               "query": str (original query)
           }
       """
   ```

### **app.py Requirements (Gradio Interface)**

1. **UI Layout**
   - Input: Single textbox for user question (placeholder: "Ask about household finance, retirement planning, tax strategy, etc.")
   - Output: Two components
     - Markdown component for formatted answer + sources
     - Optional: Info component showing retrieval stats
   - Button: "Ask" (or use default submit)
   - Title: "Household Finance Knowledge Assistant"
   - Description: "Answers questions about household investment, tax planning, and retirement strategy based on curated knowledge base (Chinese + English)"

2. **Integration Flow**
   - On user input:
     1. Call `retrieval.retrieve_and_format(query, top_k=6)` from retrieval.py
        - Gets formatted_context (string) and raw_chunks (list)
     2. Pass to `generation.generate_answer(query, formatted_context, raw_chunks)`
        - Gets dict with answer, sources, query
     3. Format output for display:
        ```
        # Answer
        {answer text}
        
        ## Sources
        {formatted source list}
        
        ---
        *Retrieved 6 chunks in {elapsed_time:.2f}s*
        ```

3. **Error Handling**
   - Catch Groq API errors: Display "Error connecting to LLM service"
   - Catch Chroma connection errors: Display "Knowledge base not available. Run ingest.py first."
   - Show query in output even if error occurs

4. **Example Gradio Skeleton**
   ```python
   import gradio as gr
   from retrieval import retrieve_and_format
   from generation import generate_answer
   
   def answer_question(query):
       # Retrieve
       formatted_context, chunks = retrieve_and_format(query, top_k=6)
       
       # Generate
       result = generate_answer(query, formatted_context, chunks)
       
       # Format output
       output = f"**Answer:**\n{result['answer']}\n\n**Sources:**\n"
       for source in result['sources']:
           output += f"- {source}\n"
       
       return output
   
   iface = gr.Interface(
       fn=answer_question,
       inputs=gr.Textbox(label="Question", placeholder="..."),
       outputs=gr.Markdown(),
       title="Household Finance Assistant",
       description="...",
       examples=[
           ["What is the 4% rule?"],
           ["How much emergency fund should I have?"],
           ["What is a Backdoor Roth IRA?"],
       ]
   )
   
   if __name__ == "__main__":
       iface.launch()
   ```

## Specifications to Enforce

### **Grounding Requirement (CRITICAL)**
- System prompt MUST include explicit instruction to use ONLY retrieved context
- If no context retrieved or context irrelevant, respond with "I don't have information about that."
- Never allow the LLM to use external knowledge
- Add a flag to track if answer is grounded or "knowledge base miss"

### **Output Format**
```
**Answer:**
[1-2 sentence direct answer grounded in context]

**Detailed Explanation:**
[Longer explanation with specific details from chunks]

**Sources:**
- [Chunk N from path/to/source.txt]
- [Chunk M from path/to/source.txt]
- ...
```

### **Multilingual Support**
- Accept queries in English or Chinese
- Pass queries as-is to Groq (multilingual model handles it)
- Responses may be English, Chinese, or mixed depending on query language

### **Evaluation Integration**
- Include a `--eval` mode that runs all 5 test questions from planning.md
- Output evaluation report with: retrieved chunks, generated answer, matches expected answer (Y/N)
- Save results to `evaluation_report.json`

### **Test Questions (From planning.md)**
```python
TEST_QUESTIONS = [
    {
        "question": "What emergency fund size does the household finance material recommend?",
        "expected_answer": "A reserve of about 3–6 months of living expenses."
    },
    {
        "question": "Which account types are described as tax-efficient for retirement savings and what is a Backdoor Roth IRA?",
        "expected_answer": "Use tax-advantaged retirement accounts, Roth for tax-free growth, and a Backdoor Roth IRA is a strategy to contribute to Roth via nondeductible traditional IRA conversions when direct Roth contributions are limited."
    },
    {
        "question": "How should families prioritize debt repayment and insurance planning?",
        "expected_answer": "Prioritize high-interest debt first and maintain adequate insurance coverage like term life, health, and property/casualty protection as part of household financial defense."
    },
    {
        "question": "What asset location guidance is given for taxable, tax-deferred, and tax-free accounts?",
        "expected_answer": "Hold tax-inefficient assets like bonds in tax-deferred accounts, tax-efficient equities in taxable or Roth accounts, and use Roth for assets expected to grow most."
    },
    {
        "question": "What is the 4% rule and what main caution is noted for retirement withdrawals?",
        "expected_answer": "Withdraw about 4% of the portfolio in the first year and adjust thereafter, while watching sequence-of-returns risk and longevity/inflation sensitivity."
    }
]
```

## Files to Generate

1. **generation.py**
   - `generate_answer(query, retrieved_context, source_chunks) → dict`
   - `run_evaluation(test_questions, output_file="evaluation_report.json")`
   - Groq client initialization with error handling
   - System prompt with grounding enforcement

2. **app.py**
   - Gradio interface with textbox input, markdown output
   - Integration of retrieval.py + generation.py
   - `--eval` CLI mode for evaluation
   - Examples in UI (3-5 sample questions)

## Verify Against Spec

✓ System prompt enforces grounding (no external knowledge)
✓ Output includes source attribution with chunk IDs and paths
✓ Groq LLM integration with fallback error messages
✓ Gradio UI is functional and user-friendly
✓ Evaluation mode runs all 5 test questions
✓ Multilingual support (English + Chinese queries)
✓ Retrieved context properly formatted and passed to LLM

## Additional Notes

- The retrieval.py module is already complete and tested. Use it directly.
- Chroma vector store already populated at ./chroma_store with 163 chunks.
- The system should handle edge cases: empty queries, network errors, no relevant chunks retrieved.
- Keep generation concise (1-2 sentences answer + detailed explanation).
- If you need to debug retrieval, test retrieval.py first: `python retrieval.py --query "emergency fund" --evaluate`
