# Dynamics 365 Business Process API

A read-only, versioned static API generated from Microsoft's official
[Dynamics 365 Business Process Catalog](https://aka.ms/BusinessProcessCatalog).

The API is designed for agents, RAPP clients, implementation accelerators, and
other tools that need stable business-process IDs and hierarchy without parsing
Excel at runtime.

## API

After GitHub Pages deployment:

```text
https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/catalog.json
https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/roots.json
https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/processes.json
https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/products.json
```

| File | Purpose |
| --- | --- |
| `catalog.json` | Version, provenance, counts, checksums, and endpoint map |
| `roots.json` | The 15 end-to-end business processes |
| `processes.json` | All six hierarchy levels in one compact collection |
| `products.json` | Product-to-process reverse index |

The July 2026 snapshot contains:

- 15 end-to-end processes
- 94 process areas
- 677 business processes
- 3,592 scenarios
- 827 system processes
- 1,628 test cases

## Examples

List end-to-end processes:

```bash
curl -fsSL \
  https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/roots.json \
  | jq '.entries[] | {id, sequence_id, title}'
```

Find direct children of Prospect to quote:

```bash
curl -fsSL \
  https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/processes.json \
  | jq '.entries[] | select(.parent_id == "d6689987c7775v0")'
```

Search locally after one download:

```bash
curl -fsSL \
  https://kowildfe_microsoft.github.io/dynamics365-business-process-api/api/v1/processes.json \
  | jq '.entries[] | select((.title + " " + (.products | join(" "))) | test("quote"; "i"))'
```

## RAPP client

`rapp/business_process_catalog_agent.py` is a read-only portable agent with
`catalog`, `roots`, `children`, `get`, `search`, and `products` actions. It
downloads the immutable JSON API and caches it in memory. It never writes to a
customer system or interprets product occurrence as licensing entitlement.

## Refreshing from Microsoft

Download the latest workbook from <https://aka.ms/BusinessProcessCatalog>, then:

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_catalog.py "/path/to/Business Process Catalog.xlsx"
python -m pytest -q
```

The generator preserves factual catalog metadata only: Microsoft ID, process
sequence ID, hierarchy, title, status, application family, products, module,
and Microsoft references. Long source descriptions and implementation content
are intentionally not redistributed.

## Authority and licensing

Microsoft's workbook is the source of truth. This repository is an unofficial
generated projection and is not an officially supported Microsoft product.
Microsoft-originated data and trademarks remain subject to Microsoft's source
terms and are not relicensed by this repository's MIT license. See
[`NOTICE.md`](NOTICE.md).
