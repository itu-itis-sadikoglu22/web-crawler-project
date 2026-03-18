# Product PRD — Single-Node Web Crawler with Concurrent Search

## 1. Overview
This project is a localhost-runnable web crawler and search system designed to run on a single machine while supporting large crawl workloads under controlled resource limits. The system exposes two main capabilities:

1. `index(origin, k)`: starts a crawl from a given origin URL up to depth `k`, ensuring the same page is not crawled more than once per crawl job.
2. `search(query)`: returns relevant indexed URLs in the form `(relevant_url, origin_url, depth)`.

The system should allow search to run while indexing is active, so newly discovered results become searchable as soon as they are indexed.

## 2. Goals
- Build a working crawler using mostly language-native functionality.
- Support bounded, controlled crawling with back pressure.
- Allow concurrent search during active indexing.
- Provide a simple CLI to:
  - start indexing
  - run search
  - view crawler state and progress
- Keep the architecture scalable on a single machine.

## 3. Non-Goals
- Distributed crawling across multiple machines
- Full browser rendering / JavaScript execution
- Production-grade ranking quality
- Advanced duplicate-content detection beyond URL normalization and optional content hashing

## 4. Assumptions
- `index` is typically invoked before `search`, but the design should support search while indexing is still active.
- Only HTML pages will be indexed.
- Relevancy can be defined using a simple keyword-based inverted index.
- The crawler runs on localhost and uses a local SQLite database.

## 5. Functional Requirements

### 5.1 Index
Given:
- `origin`: starting URL
- `k`: maximum crawl depth

The system must:
- crawl pages breadth-first or near breadth-first up to depth `k`
- avoid crawling the same normalized URL twice within the same crawl job
- extract links from HTML pages
- normalize discovered URLs before scheduling
- associate each discovered page with:
  - its `origin_url`
  - its `depth`
- persist discovered pages and indexing metadata
- apply back pressure through bounded queues and limited workers

### 5.2 Search
Given:
- `query`: string

The system must:
- tokenize the query
- search indexed content for relevant matches
- return results as triples:
  - `(relevant_url, origin_url, depth)`
- support reads while indexing is active
- reflect newly indexed pages as soon as they are committed

### 5.3 Status / Observability
The system must expose a simple CLI command for status, including:
- active crawl jobs
- pages visited
- pages indexed
- queue depth
- active worker count
- failed fetches
- whether back pressure is currently engaged

## 6. Non-Functional Requirements
- Must run locally on one machine
- Must remain responsive during active crawling
- Must avoid unbounded memory growth
- Must use mostly Python standard library components
- Must be structured for maintainability and testability

## 7. Architecture Overview

### Components
- **CLI Layer**
  - accepts commands for indexing, searching, and status
- **Crawler Manager**
  - owns crawl jobs, queueing, visited checks, and worker coordination
- **Fetcher**
  - downloads HTML content using standard library HTTP tools
- **Parser**
  - extracts links and text from HTML
- **Storage Layer**
  - persists pages, crawl jobs, discoveries, and search index in SQLite
- **Search Layer**
  - queries the inverted index and joins results with crawl metadata

## 8. Storage Design

### Suggested Tables
- `crawl_jobs`
  - job_id
  - origin_url
  - max_depth
  - status
  - created_at

- `pages`
  - url
  - normalized_url
  - title
  - body_text
  - status_code
  - fetched_at

- `discoveries`
  - job_id
  - page_url
  - origin_url
  - depth

- `frontier`
  - job_id
  - url
  - depth
  - status (`pending`, `in_progress`, `done`, `failed`)

- `inverted_index`
  - term
  - page_url
  - frequency

## 9. Concurrency Model
- Use a bounded in-memory queue for crawl tasks.
- Use a fixed-size worker pool with threads.
- Each fetched page is parsed and committed incrementally.
- Search reads from SQLite while indexing writes continue.
- SQLite WAL mode should be used to improve concurrent read/write behavior.

## 10. Back Pressure Strategy
The system should apply back pressure using:
- bounded task queue
- fixed worker count
- request timeout
- optional per-host or global rate limiting

This ensures controlled resource usage and prevents runaway queue growth.

## 11. Relevancy Definition
A page is considered relevant if one or more query tokens appear in its indexed text.
Ranking may be based on:
- number of matched query terms
- total term frequency
- optional title match bonus

## 12. Resume Strategy
If time allows, the crawler should be resumable by persisting:
- crawl jobs
- pending frontier items
- visited/discovered state
- indexed pages

On restart, pending work can be re-queued without restarting the crawl from scratch.

## 13. CLI Commands
Example commands:
- `index <origin_url> <depth>`
- `search <query>`
- `status`

Optional:
- `resume <job_id>`
- `jobs`

## 14. Deliverables
The repository should include:
- working localhost-runnable code
- `readme.md`
- `product_prd.md`
- `recommendation.md`

## 15. Implementation Priority
1. Project skeleton
2. PRD and documentation
3. SQLite schema
4. URL normalization
5. HTML fetch + parse
6. Bounded crawl queue + workers
7. Incremental inverted index
8. Search command
9. Status command
10. Resume support (optional)