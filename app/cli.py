import argparse
import time

from app.crawler import Crawler
from app.search import SearchEngine
from app.storage import Storage


def format_status(storage: Storage, crawler: Crawler | None = None) -> None:
    db_status = storage.get_status()

    print("\nSystem Status")
    print("-" * 40)
    print(f"Active jobs     : {db_status['active_jobs']}")
    print(f"Pages indexed   : {db_status['pages_indexed']}")
    print(f"Pending queue   : {db_status['pending_queue']}")
    print(f"In progress     : {db_status['in_progress']}")
    print(f"Completed       : {db_status['completed']}")
    print(f"Failed          : {db_status['failed']}")

    if crawler is not None:
        runtime = crawler.get_runtime_status()
        print(f"Runtime queue   : {runtime['queue_size']}/{runtime['max_queue_size']}")
        print(f"Active workers  : {runtime['active_workers']}/{runtime['worker_count']}")
        print(f"Back pressure   : {runtime['back_pressure_active']}")

    print("-" * 40)


def handle_index(args):
    storage = Storage()
    crawler = Crawler(
        storage=storage,
        worker_count=args.workers,
        max_queue_size=args.queue_size,
    )

    job_id = crawler.start_indexing(args.origin, args.depth)
    print(f"Started crawl job {job_id} for {args.origin} up to depth {args.depth}")

    if args.watch:
        try:
            while True:
                format_status(storage, crawler)

                runtime = crawler.get_runtime_status()
                if crawler.task_queue.unfinished_tasks == 0 and runtime["active_workers"] == 0:
                    break

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping watcher...")

    crawler.wait_until_done(job_id)
    format_status(storage, crawler)
    print("Indexing complete.")


def handle_search(args):
    storage = Storage()
    engine = SearchEngine(storage)
    results = engine.search(args.query)

    print(f"\nSearch query: {args.query}")
    print("-" * 60)

    if not results:
        print("No results found.")
        return

    for i, (relevant_url, origin_url, depth) in enumerate(results, start=1):
        print(f"{i}. relevant_url: {relevant_url}")
        print(f"   origin_url  : {origin_url}")
        print(f"   depth       : {depth}")
        print()


def handle_status(args):
    storage = Storage()
    format_status(storage)


def build_parser():
    parser = argparse.ArgumentParser(description="Single-node web crawler")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Start indexing")
    index_parser.add_argument("origin", type=str, help="Origin URL")
    index_parser.add_argument("depth", type=int, help="Maximum crawl depth")
    index_parser.add_argument("--workers", type=int, default=4, help="Number of worker threads")
    index_parser.add_argument("--queue-size", type=int, default=100, help="Maximum in-memory queue size")
    index_parser.add_argument("--watch", action="store_true", help="Show live status while indexing")
    index_parser.set_defaults(func=handle_index)

    search_parser = subparsers.add_parser("search", help="Search indexed pages")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.set_defaults(func=handle_search)

    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=handle_status)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()