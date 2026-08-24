import urllib.parse
import urllib.request
import json
import yaml

OPENALEX_BASE_URL = "https://api.openalex.org/works"


def get_JSON_from_openalex(orcid):
    if not orcid:
        raise ValueError("ORCID is required")

    query = urllib.parse.urlencode({
        "filter": f"author.orcid:{orcid}",
        "per-page": 200,
        "cursor": "*",
    })
    url = f"{OPENALEX_BASE_URL}?{query}"

    results = []
    meta = None

    while url:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode('utf-8'))

        if meta is None:
            meta = data.get("meta", {})
        results.extend(data.get("results", []))

        next_cursor = data.get("meta", {}).get("next_cursor")
        if not next_cursor:
            break

        query = urllib.parse.urlencode({
            "filter": f"author.orcid:{orcid}",
            "per-page": 200,
            "cursor": next_cursor,
        })
        url = f"{OPENALEX_BASE_URL}?{query}"

    if meta is None:
        meta = {}
    meta["retrieved_count"] = len(results)

    return {"meta": meta, "results": results}


def get_YAML_from_openalex(orcid):
    data = get_JSON_from_openalex(orcid)
    return yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

from typing import Any


def get_source_display_name_from_openalex(openalex_json: dict[str, Any], doi: str) -> str | None:
    """Devuelve el nombre de la fuente asociada a un DOI en OpenAlex."""
    if not doi:
        raise ValueError("DOI is required")

    doi_url = doi if doi.startswith("https://doi.org/") else f"https://doi.org/{doi}"

    for item in openalex_json.get("results", []):
        if item.get("ids", {}).get("doi") == doi_url:
            return item.get("primary_location", {}).get("source", {}).get(
                "display_name"
            )

    return None