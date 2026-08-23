import json
import urllib.error
import urllib.request
from urllib.parse import quote

import yaml

ZBMATH_API_URL = 'https://api.zbmath.org/v1'


def _build_request(author_ID):
    url = f"{ZBMATH_API_URL}/document/_search?search_string=ia%3A{quote(str(author_ID), safe='.-_')}"
    return urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        },
    )


def _read_json_response(request):
    try:
        with urllib.request.urlopen(request) as response:
            payload = response.read().decode('utf-8')
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"zbMATH request failed with HTTP {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"zbMATH request failed: {exc.reason}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("zbMATH returned invalid JSON") from exc


# This function retrieves the zbMATH Open publications by zbMATH author ID and returns them in JSON format
def get_JSON_from_zbmath(author_ID):
    request = _build_request(author_ID)
    return _read_json_response(request)


# This function retrieves the zbMATH Open publications by zbMATH author ID and returns them in YAML format
def get_YAML_from_zbmath(author_ID):
    data = get_JSON_from_zbmath(author_ID)
    return yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

def fix_zbmath_source(json_zbmath):
    """Repair zbMATH sources with conflicting license text.

    For each result entry, if source.source is the known placeholder text,
    replace it using values from source.series and source.
    """
    placeholder = "zbMATH Open Web Interface contents unavailable due to conflicting licenses."

    for entry in json_zbmath.get("result", []):
        source = entry.get("source", {})
        if source.get("source") != placeholder:
            continue

        series = source.get("series", {})
        parts = []

        short_title = series.get("short_title")
        if short_title:
            parts.append(short_title)

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
            parts.append(f"({year})")

        if parts:
            source["source"] = ", ".join(parts)

    return json_zbmath

def get_author_from_id(author_ID):
    url = f"{ZBMATH_API_URL}/author/{quote(str(author_ID), safe='.-_')}"
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        },
    )
    response = _read_json_response(request)
    result = response.get("result", {})
    spellings = result.get("spellings", [])
    if spellings:
        first_spelling = spellings[0]
        return {
            "given": first_spelling.get("first_name"),
            "family": first_spelling.get("last_name"),
        }

    name = result.get("name", "")
    family, separator, given = name.partition(",")
    if not separator or not family.strip() or not given.strip():
        return {}

    return {"given": given.strip(), "family": family.strip()}


def get_author_lookup_from_zbmath(json_zbmath):
    author_lookup = {}
    for entry in json_zbmath.get("result", []):
        contributors = entry.get("contributors", {})
        for author in contributors.get("authors", []):
            for code in author.get("codes", []):
                if code not in author_lookup:
                    author_lookup[code] = get_author_from_id(code)
    return author_lookup


