#!/usr/bin/env python3
"""
Gradio interface for household finance knowledge assistant.

Combines retrieval and generation into a user-friendly web interface.
Supports both CLI testing and interactive web UI.

To run:
  - Interactive UI: python app.py
  - Evaluation: python app.py --evaluate
  - Single query: python app.py --query "your question"
"""

import sys
import json
import argparse
import time
from pathlib import Path

try:
    import gradio as gr
except ImportError:
    print("Gradio not installed. Install with: pip install gradio")
    sys.exit(1)

from retrieval import retrieve_and_format, evaluate_retrieval as retrieve_evaluate
from generation import generate_answer, format_response, evaluate_on_test_questions


# Example questions for the UI
EXAMPLE_QUESTIONS = [
    ["What is the 4% rule and how does it apply to retirement withdrawals?"],
    ["How much should I have in an emergency fund?"],
    ["What is a Backdoor Roth IRA and when should I consider it?"],
    ["How should I prioritize debt repayment?"],
    ["What asset location strategy is recommended for tax efficiency?"],
]


def answer_question(query: str, show_retrieval_stats: bool = False) -> str:
    """
    Main interface function: retrieve context and generate answer.
    
    Args:
        query (str): User's question
        show_retrieval_stats (bool): Whether to include retrieval statistics
    
    Returns:
        str: Formatted answer with sources and optional stats
    """
    if not query or not query.strip():
        return "Please enter a question."

    try:
        # Retrieve relevant context
        start_time = time.time()
        formatted_context, chunks = retrieve_and_format(query, top_k=6)
        retrieval_time = time.time() - start_time

        # Generate grounded answer
        start_time = time.time()
        result = generate_answer(query, formatted_context, chunks)
        generation_time = time.time() - start_time

        # Format response
        output = format_response(result)

        # Add retrieval stats if requested
        if show_retrieval_stats:
            stats = f"\n\n---\n\n**Performance Metrics:**\n"
            stats += f"- Retrieval time: {retrieval_time:.2f}s\n"
            stats += f"- Generation time: {generation_time:.2f}s\n"
            stats += f"- Chunks retrieved: {len(chunks)}\n"
            if "tokens_used" in result:
                tokens = result["tokens_used"]
                stats += f"- Tokens used: {tokens['total']}\n"
            output += stats

        return output

    except Exception as e:
        return f"**Error:** {str(e)}\n\nPlease ensure:\n- GROQ_API_KEY is set\n- Vector store exists at ./chroma_store\n- retrieval.py and generation.py are available"


def create_gradio_interface():
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(title="Household Finance Assistant") as interface:
        gr.Markdown(
            """
# 🏠 Household Finance Knowledge Assistant

Ask questions about household investment strategy, tax planning, insurance, debt management, retirement, and estate planning.

**Powered by:**
- **Retrieval:** all-MiniLM-L6-v2 semantic search (6 chunks)
- **Generation:** Groq llama-3.3-70b-versatile with grounding constraints
- **Knowledge Base:** 80 household finance documents (Chinese + English)

All answers are grounded in the knowledge base with source attribution.
        """
        )

        with gr.Row():
            with gr.Column():
                query_input = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., What is the 4% rule? How much emergency fund should I have?",
                    lines=2,
                    scale=4,
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Ask", scale=1, variant="primary")
                    stats_check = gr.Checkbox(
                        label="Show stats",
                        value=False,
                        scale=1,
                    )

        with gr.Row():
            output = gr.Markdown(
                label="Response",
                value="Enter a question and click 'Ask' to get started.",
            )

        # Connect button
        submit_btn.click(
            fn=answer_question,
            inputs=[query_input, stats_check],
            outputs=output,
        )

        # Allow Enter key to submit
        query_input.submit(
            fn=answer_question,
            inputs=[query_input, stats_check],
            outputs=output,
        )

        # Add examples
        gr.Examples(
            examples=EXAMPLE_QUESTIONS,
            inputs=query_input,
            label="Example Questions",
        )

        gr.Markdown(
            """
---

**Tips:**
- Ask specific questions for better answers
- Queries in both English and Chinese are supported
- Source documents include tax strategy, retirement planning, insurance, debt management, and more
- If no relevant information found, the system will tell you

**Note:** This system is grounded in the knowledge base. It will not provide answers beyond what's in the source documents.
        """
        )

    return interface


def run_cli_evaluation():
    """Run evaluation mode from CLI."""
    print("\n" + "="*70)
    print("HOUSEHOLD FINANCE ASSISTANT - EVALUATION MODE")
    print("="*70)

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

    print("\nRunning generation evaluation on 5 test questions...\n")
    
    try:
        evaluate_on_test_questions(
            retrieve_and_format,
            test_questions,
            output_file="generation_evaluation_report.json"
        )
    except Exception as e:
        print(f"Error during evaluation: {e}")
        sys.exit(1)

    # Also run retrieval evaluation
    print("\n" + "="*70)
    print("RETRIEVAL EVALUATION")
    print("="*70 + "\n")

    try:
        retrieve_evaluate(test_questions, verbose=True)
    except Exception as e:
        print(f"Error during retrieval evaluation: {e}")

    print("\n" + "="*70)
    print("Evaluation complete!")
    print("="*70)


def run_cli_query(query: str):
    """Run a single query from CLI."""
    print(f"\nQuery: {query}\n")
    output = answer_question(query, show_retrieval_stats=True)
    print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Household Finance Knowledge Assistant"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to test (disables interactive UI)",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run evaluation on all 5 test questions",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public link to the Gradio interface",
    )
    parser.add_argument(
        "--server-name",
        type=str,
        default="127.0.0.1",
        help="Server name/IP for Gradio (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=7860,
        help="Server port for Gradio (default: 7860)",
    )

    args = parser.parse_args()

    if args.query:
        # Single query mode
        run_cli_query(args.query)
    elif args.evaluate:
        # Evaluation mode
        run_cli_evaluation()
    else:
        # Interactive Gradio UI
        print("\n" + "="*70)
        print("HOUSEHOLD FINANCE KNOWLEDGE ASSISTANT")
        print("="*70)
        print("\nLaunching Gradio interface...")
        print(f"Open browser at: http://{args.server_name}:{args.server_port}")
        print("\nPress Ctrl+C to stop.\n")

        interface = create_gradio_interface()
        interface.launch(
            server_name=args.server_name,
            server_port=args.server_port,
            share=args.share,
            show_error=True,
        )


if __name__ == "__main__":
    main()
