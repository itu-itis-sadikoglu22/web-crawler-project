# Web Crawler Project

This project is a simple single-machine web crawler and search tool built for a take-home systems exercise. It crawls pages starting from a given origin URL up to a specified depth, stores the discovered content locally, and lets you search across indexed pages while crawling is still in progress.

The implementation is intentionally practical and scoped. Instead of relying on full-featured crawling or search libraries, it uses mostly Python’s standard library for fetching, parsing, concurrency, and persistence. The goal was to build something small, understandable, and reasonably well-structured within the expected time frame.

## What the project can do

The system exposes two main capabilities:

### 1. Index
Starts a crawl from a given URL up to depth `k`.

Example idea:
- depth `0`: the origin page
- depth `1`: pages linked directly from the origin
- depth `2`: pages linked from those pages

While crawling, the system:
- normalizes URLs
- avoids crawling the same page twice within the same job
- extracts page text and links
- stores discovered pages in a local SQLite database
- updates the search index incrementally

### 2. Search
Searches indexed content and returns results in this format:

`(relevant_url, origin_url, depth)`

Where:
- `relevant_url` is the matched page
- `origin_url` is the crawl origin that led to this page
- `depth` is how far away the page was from that origin

Search is designed to work while indexing is still active, so newly discovered pages can start appearing in results as soon as they are processed.

## Why this design

This project was built around a few practical goals:

- keep it runnable on localhost
- use mostly language-native tools
- make indexing and search work together
- keep memory use under control
- stay simple enough to explain and maintain

To do that, the project uses:
- `urllib` for fetching pages
- `html.parser` for extracting links and text
- `sqlite3` for storage and search indexing
- `threading` and `queue` for worker coordination and back pressure

## Project structure

```text
web-crawler-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── cli.py
│   ├── crawler.py
│   ├── fetcher.py
│   ├── parser.py
│   ├── search.py
│   ├── storage.py
│   └── utils.py
├── data/
├── tests/
├── readme.md
├── product_prd.md
├── recommendation.md
├── requirements.txt
└── run.py


Some discovered URLs may fail during crawling due to network conditions, unsupported content, or remote server behavior. The crawler records these failures without interrupting the overall indexing job.