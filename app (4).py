#!/usr/bin/env python3
"""
Custom Search Engine - Web UI version.

Same engine as search_engine.py (DuckDuckGo + free Groq LLM), but with a
simple browser page instead of the command line.

Setup:
    pip install ddgs groq flask --break-system-packages

    export GROQ_API_KEY="your-free-groq-key"

Usage:
    python app.py

Then open your browser to: http://127.0.0.1:5000
"""

import os
import re
from flask import Flask, request, render_template_string
from groq import Groq
from ddgs import DDGS

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "openai/gpt-oss-20b"

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


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
    if not results:
        return "No search results were found."
    blocks = []
    for i, r in enumerate(results, start=1):
        blocks.append(
            f"[{i}] {r['title']}\nURL: {r['link']}\nSnippet: {r['snippet']}"
        )
    return "\n\n".join(blocks)


def synthesize_answer(query: str, results: list[dict]) -> str:
    context = format_results_for_llm(results)

    system_prompt = (
        "You are a search-answering assistant. You are given a user's query "
        "and a numbered list of live web search results (title, URL, "
        "snippet). Your job:\n"
        "1. Write a clear, direct answer to the query using ONLY information "
        "from the provided results.\n"
        "2. Cite claims inline using bracketed numbers matching the result "
        "list, exactly like this: [1]. Do not use any other bracket style.\n"
        "3. If results conflict, note the disagreement.\n"
        "4. If the results don't contain enough information, say so plainly "
        "instead of guessing.\n"
        "5. Keep the answer concise and well-organized. Do not fabricate "
        "sources or facts not present in the results."
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


def linkify_citations(answer_text: str, results: list[dict]) -> str:
    """Turn [1], [2], etc. into clickable superscript links to the source."""
    def replace(match):
        num = int(match.group(1))
        if 1 <= num <= len(results):
            url = results[num - 1]["link"]
            return f'<a class="cite" href="{url}" target="_blank" rel="noopener">[{num}]</a>'
        return match.group(0)

    return re.sub(r"\[(\d+)\]", replace, answer_text)


PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Argon</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,500&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
  :root {
    --void: #0A0B12;
    --deep: #171226;
    --violet: #241A38;
    --teal: #0E1C22;
    --mist: #E9E4F1;
    --muted: #948BA8;
    --line: rgba(233, 228, 241, 0.14);
    --accent: #8FD8DB;
    --accent-glow: rgba(143, 216, 219, 0.35);
    --amethyst: #B9A6E0;
    --radius: 3px;
  }

  * { box-sizing: border-box; }

  html, body { height: 100%; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--mist);
    margin: 0;
    padding: 0 24px;
    min-height: 100vh;
    background: linear-gradient(120deg, var(--void), var(--deep), var(--violet), var(--teal), var(--void));
    background-size: 400% 400%;
    animation: tide 26s ease-in-out infinite;
    position: relative;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 700px 500px at 20% 15%, rgba(143,216,219,0.10), transparent 60%),
      radial-gradient(ellipse 600px 500px at 85% 75%, rgba(185,166,224,0.10), transparent 60%);
    pointer-events: none;
    animation: drift 32s ease-in-out infinite alternate;
  }

  @keyframes tide {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  @keyframes drift {
    from { transform: translateY(-16px) scale(1); opacity: 0.9; }
    to   { transform: translateY(16px) scale(1.04); opacity: 1; }
  }

  .wrap {
    max-width: 620px;
    margin: 0 auto;
    padding: 88px 0 96px;
    position: relative;
    z-index: 1;
  }

  .brand {
    margin-bottom: 12px;
  }

  .wordmark {
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-weight: 600;
    font-size: 6rem;
    line-height: 1;
    letter-spacing: 0.01em;
    color: var(--accent);
    text-shadow: 0 0 28px var(--accent-glow);
  }

  .byline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.03em;
    color: var(--muted);
    margin: 0 0 60px;
  }

  .mark {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.03em;
    color: var(--muted);
  }

  h1 {
    font-family: 'Cormorant Garamond', serif;
    font-weight: 700;
    font-size: 3.4rem;
    line-height: 1.14;
    letter-spacing: 0.005em;
    margin: 0 0 8px;
    max-width: 14ch;
    color: var(--mist);
  }

  .rule {
    width: 64px;
    height: 1px;
    margin: 24px 0 44px;
    background: linear-gradient(90deg, var(--accent), transparent);
  }

  form { margin-bottom: 8px; }

  .field {
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 1.5px solid var(--line);
    padding-bottom: 14px;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
  }

  .field:focus-within {
    border-color: var(--accent);
    box-shadow: 0 1px 0 0 var(--accent-glow);
  }

  input[type=text] {
    flex: 1;
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.4rem;
    color: var(--mist);
    border: none;
    background: transparent;
    outline: none;
    padding: 4px 0;
  }

  input[type=text]::placeholder {
    color: #6E6684;
    font-style: italic;
  }

  button {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.01em;
    background: transparent;
    border: 1px solid var(--accent);
    color: var(--accent);
    cursor: pointer;
    padding: 9px 20px;
    border-radius: 999px;
    white-space: nowrap;
    transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
  }

  button:hover {
    background: var(--accent);
    color: var(--void);
    box-shadow: 0 0 24px var(--accent-glow);
  }

  .hint {
    font-size: 0.82rem;
    color: var(--muted);
    margin: 16px 0 0;
  }

  .result {
    margin-top: 56px;
    animation: rise 0.6s ease both;
  }

  @keyframes rise {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .answer {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.3rem;
    line-height: 1.75;
    white-space: pre-wrap;
    color: var(--mist);
    padding-bottom: 32px;
    border-bottom: 1px solid var(--line);
  }

  .cite {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68em;
    color: var(--accent);
    text-decoration: none;
    background: rgba(143, 216, 219, 0.12);
    padding: 1px 5px;
    border-radius: var(--radius);
    vertical-align: super;
  }

  .cite:hover {
    background: rgba(143, 216, 219, 0.22);
    box-shadow: 0 0 10px var(--accent-glow);
  }

  .sources { margin-top: 28px; }

  .sources ol {
    list-style: none;
    padding: 0;
    margin: 0;
    counter-reset: src;
  }

  .sources li {
    counter-increment: src;
    display: flex;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid var(--line);
    font-size: 0.92rem;
  }

  .sources li:last-child { border-bottom: none; }

  .sources li::before {
    content: counter(src);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--muted);
    padding-top: 2px;
    min-width: 1.2em;
  }

  .sources a {
    color: var(--mist);
    text-decoration: none;
    opacity: 0.85;
  }

  .sources a:hover {
    color: var(--accent);
    opacity: 1;
  }

  .error {
    margin-top: 40px;
    padding: 16px 18px;
    border-left: 2px solid var(--amethyst);
    background: rgba(185, 166, 224, 0.08);
    color: var(--amethyst);
    font-size: 0.92rem;
  }

  @media (max-width: 480px) {
    .wordmark { font-size: 3.6rem; }
    h1 { font-size: 2.3rem; }
    .field { gap: 10px; }
  }
</style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="wordmark">Argon</div>
    </div>
    <div class="byline">web search + reasoning</div>

    <h1>What do you want to know?</h1>
    <div class="rule"></div>

    <form method="POST">
      <div class="field">
        <input type="text" name="query" placeholder="Ask something…"
               value="{{ query|default('') }}" autofocus>
        <button type="submit">Search</button>
      </div>
      <p class="hint">Pulls live results from the web, then reads them for you.</p>
    </form>

    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}

    {% if answer %}
      <div class="result">
        <div class="answer">{{ answer|safe }}</div>
        <div class="sources">
          <ol>
            {% for r in results %}
              <li><a href="{{ r.link }}" target="_blank" rel="noopener">{{ r.title }}</a></li>
            {% endfor %}
          </ol>
        </div>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    answer = None
    results = []
    error = None
    query = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not GROQ_API_KEY:
            error = "GROQ_API_KEY is not set. Set it as an environment variable before running this app."
        elif not query:
            error = "Please enter a search query."
        else:
            try:
                results = web_search(query, num_results=8)
                if not results:
                    error = "No search results found for that query."
                else:
                    raw_answer = synthesize_answer(query, results)
                    answer = linkify_citations(raw_answer, results)
            except Exception as e:
                error = f"Something went wrong: {e}"

    return render_template_string(
        PAGE_TEMPLATE, answer=answer, results=results, error=error, query=query
    )


if __name__ == "__main__":
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY is not set. Set it before running, e.g.:")
        print('  $env:GROQ_API_KEY="your-key-here"')
    print("\nStarting server... open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000)
