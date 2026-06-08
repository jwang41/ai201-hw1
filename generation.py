#!/usr/bin/env python3
"""
Generation module for household finance knowledge system.

Uses Groq LLM (llama-3.3-70b-versatile) with grounding constraints:
- All answers MUST be based only on retrieved context
- If context insufficient, respond that information is not available
- Include source attribution for all answers

Groq API documentation: https://console.groq.com/docs/speech-text
"""

import os
import json
from typing import List, Dict
from pathlib import Path

from groq import Groq

# Load GROQ_API_KEY (and any other vars) from the .env file next to this
# module so it does not have to be exported into the shell manually. The
# explicit path makes this work regardless of the current working directory.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    # python-dotenv not installed: fall back to a minimal .env parser so the
    # key is still picked up (pip install -r requirements.txt for the real thing).
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        for _line in _env_path.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


# System prompt enforcing grounding and source attribution
SYSTEM_PROMPT = """You are a helpful household finance advisor. Your role is to answer questions about household investment strategy, tax planning, insurance, debt management, retirement, and estate planning based ONLY on the provided context.

**CRITICAL GROUNDING RULES:**
1. Base all answers ONLY on the retrieved context provided in the user message.
2. Do NOT use external knowledge, assumptions, or information outside the context.
3. If the context does not contain sufficient information to answer the question, respond with: "I don't have information about that in the knowledge base. The context provided does not cover this topic."
4. Cite the source document(s) your answer comes from. Each context chunk is labeled with its source in a header like "[Chunk 1 from documents/retirement.md]". When you state a fact, name the document it came from (e.g., "According to retirement.md, ...").
5. If the user asks for advice beyond the scope of the provided context, decline politely and explain what the knowledge base covers.

**OUTPUT FORMAT:**
- First paragraph: Direct answer to the question (1-2 sentences)
- Following paragraphs: Detailed explanation with specific details from the context, naming the source document for each key claim
- End with a confidence note if the answer is partially incomplete or requires additional context

Always maintain a professional, advisory tone suitable for household financial planning."""


def initialize_groq_client(api_key: str = None) -> Groq:
    """
    Initialize Groq client for LLM access.
    
    Args:
        api_key (str, optional): Groq API key. If None, uses GROQ_API_KEY environment variable.
    
    Returns:
        Groq: Initialized Groq client
    
    Raises:
        ValueError: If API key not provided and GROQ_API_KEY env var not set
    """
    if api_key is None:
        api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Groq API key not found. Set GROQ_API_KEY environment variable or pass api_key parameter."
        )
    
    return Groq(api_key=api_key)


def build_grounded_prompt(query: str, retrieved_context: str) -> str:
    """
    Build a grounded user prompt that includes retrieved context.
    
    The prompt explicitly instructs the model to answer only from the provided context.
    
    Args:
        query (str): User's question (English or Chinese)
        retrieved_context (str): Formatted context from retrieval module with chunk headers
    
    Returns:
        str: Complete prompt for the LLM
    """
    prompt = f"""RETRIEVED CONTEXT:
{retrieved_context}

---

USER QUESTION:
{query}

---

INSTRUCTIONS:
- Answer the user's question ONLY using the retrieved context above.
- If the context does not answer the question, say so explicitly.
- Cite the source document by name when stating a fact. Each chunk header shows its source as "[Chunk N from <source>]" — refer to that source name (e.g., "According to retirement.md, ...") rather than the chunk number.
- Maintain professional advisory tone suitable for household financial planning.
- If the answer requires multiple steps or considerations, organize them clearly.

ANSWER:"""
    return prompt


def generate_answer(
    query: str,
    retrieved_context: str,
    source_chunks: List[Dict],
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.3,
    max_tokens: int = 500,
) -> Dict:
    """
    Generate grounded answer using Groq LLM.
    
    Args:
        query (str): User's question (English or Chinese)
        retrieved_context (str): Formatted context from retrieval.format_retrieval_context()
        source_chunks (List[Dict]): Raw chunks from retrieval.retrieve_chunks()
        model (str): Groq model identifier (default: llama-3.3-70b-versatile)
        temperature (float): LLM temperature (default: 0.3 for conservative answers)
        max_tokens (int): Max output tokens (default: 500)
    
    Returns:
        Dict with keys:
            - "answer": str (LLM response, with a "**Sources:**" attribution line appended)
            - "sources": List[str] (formatted per-chunk source attribution)
            - "source_documents": List[str] (unique document names the answer drew from)
            - "query": str (original query)
            - "grounded": bool (True if answer generated from context)
            - "model": str (model used)
    """
    try:
        client = initialize_groq_client()
    except ValueError as e:
        return {
            "answer": f"Error: {e}",
            "sources": [],
            "query": query,
            "grounded": False,
            "model": model,
            "error": str(e),
        }

    # Check if context is empty
    if not retrieved_context or retrieved_context.strip() == "No relevant documents found.":
        return {
            "answer": "I don't have information about that in the knowledge base. No relevant documents were retrieved for your question.",
            "sources": [],
            "query": query,
            "grounded": False,
            "model": model,
            "error": "No relevant context retrieved",
        }

    # Build grounded prompt
    user_prompt = build_grounded_prompt(query, retrieved_context)

    try:
        # Call Groq API
        message = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        answer_text = message.choices[0].message.content.strip()

        # Extract source attribution
        sources = _format_sources(source_chunks)
        source_documents = _unique_source_names(source_chunks)

        # Programmatically append source attribution to the answer so the
        # response always names the document(s) it came from, even if the
        # model omitted an inline citation.
        if source_documents:
            answer_text += "\n\n**Sources:** " + ", ".join(source_documents)

        return {
            "answer": answer_text,
            "sources": sources,
            "source_documents": source_documents,
            "query": query,
            "grounded": True,
            "model": model,
            "tokens_used": {
                "input": message.usage.prompt_tokens,
                "output": message.usage.completion_tokens,
                "total": message.usage.total_tokens,
            },
        }

    except Exception as e:
        return {
            "answer": f"Error generating answer: {e}",
            "sources": [],
            "query": query,
            "grounded": False,
            "model": model,
            "error": str(e),
        }


def _format_sources(source_chunks: List[Dict]) -> List[str]:
    """
    Format source chunks for display.
    
    Args:
        source_chunks (List[Dict]): List of chunk dicts from retrieval.retrieve_chunks()
    
    Returns:
        List[str]: Formatted source strings
    """
    sources = []
    for i, chunk in enumerate(source_chunks, 1):
        source_path = chunk.get("source", "unknown")
        chunk_id = chunk.get("id", f"chunk_{i}")
        sources.append(f"Chunk {i}: {source_path} (ID: {chunk_id})")
    return sources


def _unique_source_names(source_chunks: List[Dict]) -> List[str]:
    """
    Extract the unique source document names from the retrieved chunks,
    preserving the order in which they were retrieved.

    Used to programmatically attribute the answer to the document(s) it came
    from. Paths are reduced to their base file name for readability
    (e.g., "documents/retirement.md" -> "retirement.md").

    Args:
        source_chunks (List[Dict]): List of chunk dicts from retrieval.retrieve_chunks()

    Returns:
        List[str]: Unique document names in retrieval order
    """
    seen = set()
    names = []
    for chunk in source_chunks:
        source_path = chunk.get("source", "unknown")
        name = os.path.basename(source_path) or source_path
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def format_response(result: Dict) -> str:
    """
    Format the generation result for display to user.
    
    Args:
        result (Dict): Output from generate_answer()
    
    Returns:
        str: Formatted response with answer and sources
    """
    output_parts = []

    # Add answer
    output_parts.append("## Answer\n")
    if "error" in result and result.get("error"):
        output_parts.append(f"**⚠️ Error:** {result['error']}\n")
    else:
        output_parts.append(result["answer"])
        output_parts.append("\n")

    # Add grounding status
    if result.get("grounded"):
        output_parts.append("\n✓ This answer is grounded in the knowledge base.\n")
    else:
        output_parts.append("\n⚠️ This answer may not be grounded in the knowledge base.\n")

    # Add sources
    if result.get("sources"):
        output_parts.append("\n## Sources\n")
        for source in result["sources"]:
            output_parts.append(f"- {source}\n")
    else:
        output_parts.append("\n*No relevant sources found.*\n")

    # Add token usage if available
    if "tokens_used" in result:
        tokens = result["tokens_used"]
        output_parts.append(
            f"\n---\n*Token usage: {tokens['input']} input + {tokens['output']} output = {tokens['total']} total*\n"
        )

    return "".join(output_parts)


def evaluate_on_test_questions(
    retrieval_fn,
    test_questions: List[Dict],
    output_file: str = "evaluation_report.json",
) -> Dict:
    """
    Evaluate the generation system on test questions.
    
    Args:
        retrieval_fn: Function to call for retrieval (e.g., retrieval.retrieve_and_format)
        test_questions (List[Dict]): List of dicts with 'question' and 'expected_answer' keys
        output_file (str): Path to save evaluation results
    
    Returns:
        Dict: Evaluation results
    """
    results = {
        "total_questions": len(test_questions),
        "questions": [],
    }

    for q_num, q_dict in enumerate(test_questions, 1):
        question = q_dict.get("question", "")
        expected = q_dict.get("expected_answer", "")

        if not question:
            continue

        print(f"\n{'='*70}")
        print(f"Question {q_num}/{len(test_questions)}: {question}")
        print(f"Expected: {expected}\n")

        # Retrieve context
        formatted_context, chunks = retrieval_fn(question)

        # Generate answer
        result = generate_answer(question, formatted_context, chunks)

        # Store result
        question_result = {
            "question_number": q_num,
            "question": question,
            "expected_answer": expected,
            "generated_answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "grounded": result.get("grounded", False),
            "model": result.get("model", ""),
            "chunks_retrieved": len(chunks),
            "error": result.get("error"),
        }

        results["questions"].append(question_result)

        print(f"Generated: {result.get('answer', '')}\n")
        print(f"Sources retrieved: {len(chunks)}")
        print(f"Grounded: {result.get('grounded')}")

    # Save results to file
    output_path = Path(output_file)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{'='*70}")
    print(f"Evaluation complete. Results saved to {output_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generation module for household finance QA system")
    parser.add_argument(
        "--query",
        type=str,
        help="Query string to test generation",
    )
    parser.add_argument(
        "--context",
        type=str,
        help="Optional context string (for testing without retrieval)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run evaluation on all 5 test questions",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_report.json",
        help="Output file for evaluation results",
    )

    args = parser.parse_args()

    if args.query:
        print(f"Query: {args.query}\n")

        if args.context:
            # Use provided context
            context = args.context
            chunks = [{"source": "manual", "id": "test"}]
        else:
            # Retrieve context
            try:
                from retrieval import retrieve_and_format

                context, chunks = retrieve_and_format(args.query, top_k=6)
            except ImportError:
                print("Error: retrieval module not found. Provide --context manually or ensure retrieval.py is available.")
                exit(1)

        # Generate answer
        result = generate_answer(args.query, context, chunks)
        output = format_response(result)
        print(output)

    elif args.evaluate:
        print("Running evaluation on test questions...")

        try:
            from retrieval import retrieve_and_format
        except ImportError:
            print("Error: retrieval module not found. Ensure retrieval.py is available.")
            exit(1)

        test_questions = [
            {
                "question": "What emergency fund size does the household finance material recommend?",
                "expected_answer": "A reserve of about 3–6 months of living expenses.",
            },
            {
                "question": "Which account types are described as tax-efficient for retirement savings and what is a Backdoor Roth IRA?",
                "expected_answer": "Use tax-advantaged retirement accounts, Roth for tax-free growth, and a Backdoor Roth IRA is a strategy to contribute to Roth via nondeductible traditional IRA conversions when direct Roth contributions are limited.",
            },
            {
                "question": "How should families prioritize debt repayment and insurance planning?",
                "expected_answer": "Prioritize high-interest debt first and maintain adequate insurance coverage like term life, health, and property/casualty protection as part of household financial defense.",
            },
            {
                "question": "What asset location guidance is given for taxable, tax-deferred, and tax-free accounts?",
                "expected_answer": "Hold tax-inefficient assets like bonds in tax-deferred accounts, tax-efficient equities in taxable or Roth accounts, and use Roth for assets expected to grow most.",
            },
            {
                "question": "What is the 4% rule and what main caution is noted for retirement withdrawals?",
                "expected_answer": "Withdraw about 4% of the portfolio in the first year and adjust thereafter, while watching sequence-of-returns risk and longevity/inflation sensitivity.",
            },
        ]

        evaluate_on_test_questions(retrieve_and_format, test_questions, args.output)

    else:
        print("Use --query to test generation or --evaluate to run evaluation")
        print("Example: python generation.py --query 'What is the 4% rule?'")
        print("Example: python generation.py --evaluate")
