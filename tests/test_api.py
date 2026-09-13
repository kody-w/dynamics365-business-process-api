import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "api" / "v1"


def load(name):
    return json.loads((API / name).read_text(encoding="utf-8"))


def test_static_api_is_complete_and_cross_referenced():
    catalog = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    roots = load("roots.json")
    processes = load("processes.json")
    products = load("products.json")

    assert catalog["schema"] == "rapp-static-api/1.0"
    assert catalog["summary"] == {
        "entries": 6833,
        "business_process": 677,
        "end_to_end": 15,
        "process_area": 94,
        "scenario": 3592,
        "system_process": 827,
        "test_case": 1628,
    }
    assert len(processes["entries"]) == 6833
    assert len(roots["entries"]) == 15
    ids = {entry["id"] for entry in processes["entries"]}
    assert len(ids) == 6833
    assert all(
        entry["parent_id"] in ids
        for entry in processes["entries"]
        if entry["parent_id"]
    )
    assert {entry["id"] for entry in roots["entries"]} == {
        entry["id"]
        for entry in processes["entries"]
        if entry["level"] == "end_to_end"
    }
    assert products["products"]


def test_catalog_checksums_match_static_files():
    catalog = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
    for entry in catalog["entries"]:
        endpoint = API / f"{entry['name']}.json"
        assert hashlib.sha256(endpoint.read_bytes()).hexdigest() == entry["sha256"]
        version = ROOT / "versions" / entry["name"] / f"{entry['sha8']}.json"
        assert version.read_bytes() == endpoint.read_bytes()


def test_rapp_agent_reads_static_files(monkeypatch):
    path = ROOT / "rapp" / "business_process_catalog_agent.py"
    spec = importlib.util.spec_from_file_location("catalog_agent", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Response:
        def __init__(self, data):
            self.data = data

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return self.data

    def local_urlopen(request, timeout):
        name = request.full_url.rsplit("/", 1)[-1]
        return Response((API / name).read_bytes())

    monkeypatch.setattr(module, "urlopen", local_urlopen)
    agent = module.BusinessProcessCatalogAgent()
    status = agent.perform(action="catalog")
    assert status["schema"] == "rapp-d365-business-processes-status/1.0"
    roots = agent.perform(action="roots")
    assert roots["count"] == 15
    search = agent.perform(action="search", query="prospect quote")
    assert any(entry["title"] == "Prospect to quote" for entry in search["entries"])
