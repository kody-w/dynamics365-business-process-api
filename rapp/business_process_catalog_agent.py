"""Read-only RAPP client for the Dynamics 365 Business Process static API."""
from __future__ import annotations

import json
from urllib.request import Request, urlopen

try:
    from basic_agent import BasicAgent
except ImportError:
    class BasicAgent:
        def __init__(self, name=None, metadata=None):
            self.name = name
            self.metadata = metadata


DEFAULT_BASE_URL = (
    "https://kowildfe_microsoft.github.io/"
    "dynamics365-business-process-api/api/v1"
)


class BusinessProcessCatalogAgent(BasicAgent):
    def __init__(self):
        self.name = "Dynamics 365 Business Process Catalog"
        self.metadata = {
            "name": self.name,
            "description": (
                "Search and navigate the read-only official Dynamics 365 business "
                "process catalog projection."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["catalog", "roots", "children", "get", "search", "products"],
                    },
                    "process_id": {"type": "string"},
                    "query": {"type": "string"},
                    "product": {"type": "string"},
                    "limit": {"type": "integer"},
                    "base_url": {"type": "string"},
                },
                "required": ["action"],
            },
        }
        self._cache = {}
        super().__init__(self.name, self.metadata)

    def _load(self, name, base_url):
        key = (base_url, name)
        if key not in self._cache:
            url = f"{base_url.rstrip('/')}/{name}.json"
            request = Request(url, headers={"Accept": "application/json"})
            with urlopen(request, timeout=15) as response:
                body = response.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024:
                raise ValueError("Catalog response exceeds the size limit.")
            self._cache[key] = json.loads(body)
        return self._cache[key]

    def perform(
        self,
        action="catalog",
        process_id="",
        query="",
        product="",
        limit=25,
        base_url=DEFAULT_BASE_URL,
        **_kwargs,
    ):
        bounded = max(1, min(int(limit or 25), 100))
        if action == "catalog":
            return self._load("catalog", base_url)
        if action == "products":
            rows = self._load("products", base_url)["products"]
            if product:
                rows = [row for row in rows if product.casefold() in row["name"].casefold()]
            return {"products": rows[:bounded]}

        entries = self._load("processes", base_url)["entries"]
        if action == "roots":
            rows = [entry for entry in entries if entry["level"] == "end_to_end"]
        elif action == "children":
            if not process_id:
                raise ValueError("children requires process_id.")
            rows = [entry for entry in entries if entry["parent_id"] == process_id]
        elif action == "get":
            if not process_id:
                raise ValueError("get requires process_id.")
            rows = [entry for entry in entries if entry["id"] == process_id]
        elif action == "search":
            if not query.strip():
                raise ValueError("search requires query.")
            terms = query.casefold().split()
            rows = [
                entry
                for entry in entries
                if all(
                    term in " ".join(
                        [
                            entry["sequence_id"],
                            entry["title"],
                            " ".join(entry["application_families"]),
                            " ".join(entry["products"]),
                            entry["module"],
                        ]
                    ).casefold()
                    for term in terms
                )
            ]
        else:
            raise ValueError("Unsupported action.")
        return {"count": len(rows), "entries": rows[:bounded]}
