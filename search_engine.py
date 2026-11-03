#!/usr/bin/env python3
"""
Custom Search Engine: DuckDuckGo search + Groq (free LLM API) synthesis.

100% free. No credit card, no billing, no Google Cloud project needed
anywhere in this pipeline.

Flow:
1. Take a user query
2. Fetch real results from DuckDuckGo (via the `ddgs` package - no key needed)
3. Feed those results to a free Groq-hosted LLM, which reads them and writes
   a synthesized, cited answer (like a mini Perplexity)

Setup:
    pip install ddgs groq --break-system-packages

    export GROQ_API_KEY="your-free-groq-key"

    Get a free key (no card required) at: https://console.groq.com/keys

Usage:
    python search_engine.py "your query here"
    python search_engine.py            # interactive mode
"""

import os
import sys
from groq import Groq
from ddgs import DDGS

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "openai/gpt-oss-20b"


def check_config():
    if not GROQ_API_KEY:
        print("Missing environment variable: GROQ_API_KEY")
        print("Get a free key (no credit card needed) at:")
        print("  https://console.groq.com/keys")
        print('Then set it, e.g.:\n  export GROQ_API_KEY="..."')
        sys.exit(1)


def web_search(query: str, num_results: int = 8) -> list[dict]:
    """Query DuckDuckGo and return a list of results. No API key required."""
    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=num_results):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("href", ""),
                "snippet": item.get("body", ""),
            })
    return results


def format_results_for_llm(results: list[dict]) -> str:
    """Turn raw search results into a numbered context block for the LLM."""
    if not results:
        return "No search results were found."

    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(
            f"[{i}] {r['title']}\n"
            f"URL: {r['link']}\n"
            f"Snippet: {r['snippet']}"
        )
    return "\n\n".join(blocks)


def synthesize_answer(query: str, results: list[dict], client: Groq) -> str:
    """Ask the LLM to read the search results and produce a cited answer."""
    context = format_results_for_llm(results)

    system_prompt = (
        "You are a search-answering assistant. You are given a user's query "
        "and a numbered list of live web search results (title, URL, "
        "snippet). Your job:\n"
        "1. Write a clear, direct answer to the query using ONLY information "
        "from the provided results.\n"
        "2. Cite claims inline using bracketed numbers matching the result "
        "list, e.g. 'Paris is the capital of France [1].'\n"
        "3. If results conflict, note the disagreement.\n"
        "4. If the results don't contain enough information, say so plainly "
        "instead of guessing.\n"
        "5. Keep the answer concise and well-organized. Do not fabricate "
        "sources or facts not present in the results.\n"
        "6. After the answer, list the sources you cited as 'Sources:' with "
        "their number, title, and URL."
    )

    user_message = f"Query: {query}\n\nSearch results:\n\n{context}"

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content


def run_query(query: str, client: Groq, num_results: int = 8):
    print(f"\nSearching for: {query}\n")
    try:
        results = web_search(query, num_results=num_results)
    except Exception as e:
        print(f"Search error: {e}")
        return

    if not results:
        print("No results found for that query.")
        return

    print(f"Found {len(results)} results. Asking the LLM to synthesize an answer...\n")

    try:
        answer = synthesize_answer(query, results, client)
    except Exception as e:
        print(f"LLM error: {e}")
        return

    print("=" * 70)
    print(answer)
    print("=" * 70)


def main():
    check_config()
    client = Groq(api_key=GROQ_API_KEY)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_query(query, client)
        return

    print("Custom Search Engine (DuckDuckGo + Groq, 100% free). Type 'quit' to exit.\n")
    while True:
        try:
            query = input("Search> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not query:
            continue
        if query.lower() in ("quit", "exit"):
            break
        run_query(query, client)


if __name__ == "__main__":
    main()
