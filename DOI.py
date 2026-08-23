import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


def load_yaml_file(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def strip_latex(text: str) -> str:
    text = re.sub(r"\\\(([^)]*)\\\)", r"\1", text)
    text = re.sub(r"\\\[([^]]*)\\\]", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[A-Za-z]+\b", "", text)
    text = re.sub(r"\$([^$]*)\$", r"\1", text)
    text = re.sub(r"\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\^\{([^}]*)\}", r"\1", text)
    text = re.sub(r"_\{([^}]*)\}", r"\1", text)
    return text


def normalize_doi(doi: str) -> str:
    doi_text = doi.strip()
    doi_text = re.sub(r"^https?://doi\.org/", "", doi_text, flags=re.IGNORECASE)
    return doi_text


def normalize_title(title: str) -> str:
    normalized = strip_latex(title)
    normalized = re.sub(r"[\u2010-\u2015\u2212]", "-", normalized)
    return " ".join(normalized.split()).strip()


def build_openalex_lookup(openalex_results: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    exact: Dict[str, List[str]] = {}
    lower: Dict[str, List[str]] = {}

    for item in openalex_results:
        title = item.get("title")
        doi = item.get("doi")
        if not title or not doi:
            continue

        doi_text = normalize_doi(str(doi))
        if "arxiv" in doi_text.lower():
            continue

        normalized = normalize_title(str(title))
        lower_key = normalized.lower()
        exact.setdefault(normalized, []).append(doi_text)
        lower.setdefault(lower_key, []).append(doi_text)

    return exact, lower


def get_arxiv_identifier_from_zbmath_item(item: Dict[str, Any]) -> Optional[str]:
    for link in item.get("links", []):
        if link.get("type") == "arxiv":
            identifier = link.get("identifier")
            if identifier:
                return str(identifier).strip()
    return None


def is_year_after_2020(item: Dict[str, Any]) -> bool:
    year_value = item.get("year")
    if isinstance(year_value, str):
        year_value = year_value.strip()
        if year_value.isdigit():
            return int(year_value) > 2020
    return False


def format_arxiv_doi(arxiv_id: str) -> str:
    normalized = arxiv_id.strip()
    normalized = re.sub(r"(?i)^arxiv:\s*", "", normalized)
    return f"10.48550/arXiv.{normalized}"


def get_doi_from_zbmath_item(item: Dict[str, Any], openalex_exact: Dict[str, List[str]], openalex_lower: Dict[str, List[str]]) -> Tuple[Optional[str], Optional[str]]:
    for link in item.get("links", []):
        if link.get("type") == "doi":
            identifier = link.get("identifier")
            if identifier:
                return normalize_doi(str(identifier)), item.get("title", {}).get("title") if isinstance(item.get("title", {}), dict) else None

    title_container = item.get("title", {})
    if not isinstance(title_container, dict):
        return None, None

    title = title_container.get("title")
    normalized = normalize_title(str(title)) if title else ""
    candidates = openalex_exact.get(normalized) or openalex_lower.get(normalized.lower())
    if candidates:
        return candidates[0], title if isinstance(title, str) else None

    # arxiv_identifier = get_arxiv_identifier_from_zbmath_item(item)
    # if arxiv_identifier:
    #     return format_arxiv_doi(arxiv_identifier), item.get("title", {}).get("title") if isinstance(item.get("title", {}), dict) else None

    return None, title if isinstance(title, str) else None


def get_doi_list_from_yaml_files(zbmath_yaml_path: str, openalex_yaml_path: str) -> List[str]:
    zbmath_data = load_yaml_file(zbmath_yaml_path)
    openalex_data = load_yaml_file(openalex_yaml_path)

    openalex_results = openalex_data.get("results", [])
    openalex_exact, openalex_lower = build_openalex_lookup(openalex_results)

    doi_list: List[str] = []
    for item in zbmath_data.get("result", []):
        doi, title = get_doi_from_zbmath_item(item, openalex_exact, openalex_lower)
        if doi is None:
            title_text = title if title else "<missing title>"
            print(f"Warning: no DOI found for title: {title_text}", file=sys.stderr)
            continue
        doi_list.append(doi)

    return doi_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract DOIs from zbmath.yaml with OpenAlex fallback")
    parser.add_argument("--zbmath", default="zbmath.yaml", help="Path to zbmath.yaml")
    parser.add_argument("--openalex", default="openalex.yaml", help="Path to openalex.yaml")
    parser.add_argument("--json", action="store_true", help="Print output as JSON")
    args = parser.parse_args()

    doi_list = get_doi_list_from_yaml_files(args.zbmath, args.openalex)

    if args.json:
        print(json.dumps(doi_list, indent=2, ensure_ascii=False))
        return

    for doi in doi_list:
        print(doi if doi is not None else "")


if __name__ == "__main__":
    main()
