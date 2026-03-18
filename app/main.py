from app.crawler import Crawler
from app.storage import Storage


def main():
    storage = Storage()
    crawler = Crawler(storage=storage, worker_count=4, max_queue_size=100)

    job_id = crawler.start_indexing("https://example.com", 1)
    print(f"Started job: {job_id}")

    crawler.wait_until_done()

    print("Crawl finished.")
    print("DB status:", storage.get_status())
    print("Runtime status:", crawler.get_runtime_status())


if __name__ == "__main__":
    main()