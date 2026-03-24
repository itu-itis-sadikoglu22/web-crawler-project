# https://github.com/itu-itis-sadikoglu22/web-crawler-project

# Web Crawler Project

This project is a single-machine web crawler and search tool built for a take-home systems exercise. Given an origin URL and a depth limit, it crawls pages, stores discovered content locally, and supports searching indexed pages while crawling is still in progress.

The implementation is intentionally scoped and practical. It focuses on the core crawler behavior, local persistence, incremental search indexing, and controlled resource usage rather than a richer browser-based demo. The prompt allowed either a simple UI or CLI, so this project uses a CLI-first approach.

## Core capabilities

### Index
The crawler exposes an indexing flow equivalent to `index(origin, k)`:
- `origin` is the starting URL
- `k` is the maximum crawl depth measured in hops from the origin

During indexing, the system:
- normalizes discovered URLs
- avoids crawling the same normalized URL twice within the same crawl job
- fetches and parses HTML pages
- extracts visible text and outgoing links
- stores page content and crawl metadata in SQLite
- updates the search index incrementally as pages are processed

### Search
The crawler exposes a search flow equivalent to `search(query)`.

Search returns results in the form:

`(relevant_url, origin_url, depth)`

where:
- `relevant_url` is the indexed page that matched the query
- `origin_url` is the origin URL of the crawl job in which it was discovered
- `depth` is the hop distance from that origin

Because indexed pages are written to SQLite incrementally, newly discovered content can become searchable without waiting for the crawl to fully complete.

## Design overview

This implementation uses mostly Python’s standard library:
- `urllib` for HTTP fetching
- `html.parser` for link and text extraction
- `sqlite3` for local persistence and inverted indexing
- `threading` and `queue` for worker coordination and back pressure

The crawler runs entirely on localhost and stores its data in a local SQLite database at `data/crawler.db`.

## Back pressure and load control

To keep the crawler stable on a single machine, it includes a few simple back pressure mechanisms:
- a bounded in-memory task queue
- a fixed-size worker pool
- request timeouts
- controlled scheduling of discovered links

This prevents unbounded work generation and keeps memory usage under control as the crawl grows.

## How it works

When a crawl starts, the system creates a crawl job using the given origin URL and depth limit. The origin URL is normalized and inserted into the crawl frontier. Worker threads fetch pages from a bounded queue, parse links and text, store page content in SQLite, and schedule newly discovered links as long as they remain within the allowed depth.

The search path reads from the same database and uses a simple inverted index. This makes search available while indexing is still active. Duplicate crawling is prevented within each crawl job by normalizing URLs and tracking visited URLs per job.

## Running the project

### 1. Create a virtual environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate

### 2. Start indecxing

python -m app.main index https://example.com 1 --watch
or
python -m app.main index https://docs.python.org/3/ 1 --workers 4 --queue-size 100 --watch

### 3. Search indexed pages

python -m app.main search python


### 4. View system status

python -m app.main status


The status output includes:

active jobs
indexed pages
pending queue size
items in progress
completed items
failed items
worker activity
back pressure status
Search relevance

Relevance is intentionally simple for this exercise. A page is considered relevant if one or more query tokens appear in its indexed text. Results are ranked using a basic term-frequency-based score from the inverted index.

Notes and limitations

This is a deliberately scoped implementation for a short take-home exercise, not a production crawler.

A few things are intentionally kept simple:

only HTML pages are indexed
there is no JavaScript rendering
robots.txt is not yet handled
ranking is basic keyword matching with term frequency
the system runs on one machine only
resume after interruption is only partially prepared through persisted frontier state, but not fully implemented

Some discovered URLs may fail during crawling because of network conditions, unsupported content, redirects, SSL issues, or remote server behavior. These failures are recorded without interrupting the overall indexing job.

Deliverables included

The repository includes:

the runnable crawler and search implementation
product_prd.md
readme.md
recommendation.md