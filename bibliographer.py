#!.venv/bin/python3
import yaml
from typing import Any, Dict, Optional

from zbmath import get_JSON_from_zbmath, get_author_lookup_from_zbmath
from openalex import get_JSON_from_openalex

from DOI import *
from crossref import *
from arxiv import *

ORCID = "0000-0001-8457-9889"
zbMATH = "muro.fernando"
OUTPUT_YAML = "output.yaml"

def complete_zbmath(zbmath_data: Dict[str, Any], openalex_data: Dict[str, Any], arxiv_data: Dict[str, Any]) -> Dict[str, Any]:
    openalex_results = openalex_data.get("results", [])
    openalex_exact, openalex_lower = build_openalex_lookup(openalex_results)
    conflict_str = "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
    authors = get_author_lookup_from_zbmath(zbmath_data)

    for item in zbmath_data.get("result", []):
        arxiv_ID = get_arxiv_identifier_from_zbmath_item(item)
        if arxiv_ID:
            item["arxiv"] = arxiv_ID

        item["year"] = int(item["year"])

        if arxiv_ID and item["datestamp"][0] == "0":
            item["datestamp"] = extract_published_date(arxiv_data, arxiv_ID)

        contributors = item.get("contributors", {})
        authors_list = []
        for author_item in contributors.get("authors", []):
            codes = author_item.get("codes", [])
            if not codes:
                continue
            author_data = authors.get(codes[0])
            if author_data is not None:
                authors_list.append(author_data)
        item["authors"] = authors_list

        doi, _ = get_doi_from_zbmath_item(item, openalex_exact, openalex_lower)
        if doi:
            item["doi"] = doi
            try:
                item["bibtex"] = get_paper_bibtex_from_crossref(doi)
            except Exception:
                pass
        elif arxiv_ID:
            try:
                item["bibtex"] = get_paper_bibtex_from_arxiv(arxiv_ID)
            except Exception:
                pass

        if doi and item["document_type"]["code"] not in ("a", "j"):
            try:
                item["source"]["source"] += ", to appear in " + get_source_display_name_from_openalex(openalex_data, doi)
            except Exception:
                pass

        if arxiv_ID:
            try:
                item["abstract"] = extract_arxiv_summary(arxiv_data, arxiv_ID)
            except Exception:
                print(f"Failed to retrieve abstract for arXiv ID {arxiv_ID}")

        if doi is not None and any(
            item.get("source", {}).get(field) == conflict_str
            for field in ("pages", "source")
        ) or item.get("title", {}).get("title") == conflict_str:
            crossref_json = {}
            if doi is not None:
                try:
                    crossref_json = get_paper_JSON_from_crossref(doi)
                except Exception:
                    crossref_json = {}

            message = crossref_json.get("message") if isinstance(crossref_json, dict) else {}

            source = item.setdefault("source", {})
            if source.get("pages") == conflict_str:
                page_value = message.get("page")
                if page_value:
                    source["pages"] = page_value

            title_container = item.setdefault("title", {})
            if title_container.get("title") == conflict_str:
                title_values = message.get("title")
                if isinstance(title_values, list) and title_values:
                    title_container["title"] = title_values[0]
                elif isinstance(title_values, str):
                    title_container["title"] = title_values

            if source.get("source") == conflict_str:
                series = source.get("series", {}) or {}
                if isinstance(series, list) and series:
                    series = series[0] if isinstance(series[0], dict) else {}
                if not isinstance(series, dict):
                    series = {}

                parts = []
                short_title = series.get("short_title")
                if short_title:
                    parts.append(str(short_title))
                volume = series.get("volume")
                if volume:
                    parts.append(str(volume))
                issue = series.get("issue")
                if issue:
                    parts.append(f"No. {issue}")
                pages = source.get("pages")
                if pages:
                    parts.append(str(pages))
                year = series.get("year")
                if year:
                    parts.append(f"({year}).")
                if parts:
                    if len(parts) == 1:
                        source["source"] = parts[0]
                    elif len(parts) == 2:
                        source["source"] = " ".join(parts)
                    else:
                        source["source"] = (
                            f"{parts[0]} {', '.join(parts[1:-1])} "
                            f"{parts[-1]}"
                        )

    return zbmath_data


def main() -> None:
    zbmath_data = get_JSON_from_zbmath(zbMATH)
    openalex_data = get_JSON_from_openalex(ORCID)
    arxiv_data = get_JSON_from_arXiv(ORCID)
    output_data = complete_zbmath(zbmath_data, openalex_data, arxiv_data)

    with open(OUTPUT_YAML, "w", encoding="utf-8") as handle:
        yaml.dump(output_data, handle, sort_keys=False, allow_unicode=True, default_flow_style=False)

    print(f"Wrote {OUTPUT_YAML}")


if __name__ == "__main__":
    main()