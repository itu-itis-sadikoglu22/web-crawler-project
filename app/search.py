from app.storage import Storage
from app.utils import tokenize


class SearchEngine:
    def __init__(self, storage: Storage):
        self.storage = storage

    def search(self, query: str) -> list[tuple[str, str, int]]:
        terms = tokenize(query)
        rows = self.storage.search(terms)

        results = []
        for row in rows:
            results.append(
                (
                    row["relevant_url"],
                    row["origin_url"],
                    row["depth"],
                )
            )
        return results