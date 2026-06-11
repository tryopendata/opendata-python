from __future__ import annotations

import re


def parse_dataset_refs(sql: str) -> list[tuple[str, str]]:
    """Extract (provider, dataset) pairs from FROM/JOIN clauses in SQL.

    Handles three reference forms:
      - ``fred/gdp``           unquoted slash
      - ``"fred/gdp"``         quoted slash
      - ``fred.gdp``           dot form
      - ``fred."cpi-u"``       dot with quoted dataset

    Returns deduplicated list of (provider, dataset) tuples.
    """
    refs: list[tuple[str, str]] = []
    seen: set[str] = set()

    # Match all table ref forms after FROM/JOIN:
    #   "provider/dataset"          quoted slash
    #   provider/dataset            unquoted slash
    #   provider."dataset"          dot with quoted dataset
    #   provider.dataset            unquoted dot
    pattern = re.compile(
        r"\b(?:FROM|JOIN)\s+"
        r"(?:"
        r'"([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)"'  # quoted slash
        r'|([a-zA-Z0-9_-]+)[./]"([a-zA-Z0-9_-]+)"'  # dot/slash with quoted dataset
        r"|([a-zA-Z0-9_-]+)[./]([a-zA-Z0-9_-]+)"  # unquoted dot or slash
        r")",
        re.IGNORECASE,
    )

    for match in pattern.finditer(sql):
        provider = match.group(1) or match.group(3) or match.group(5) or ""
        dataset = match.group(2) or match.group(4) or match.group(6) or ""
        key = f"{provider}/{dataset}"

        if provider and dataset and key not in seen:
            seen.add(key)
            refs.append((provider, dataset))

    return refs


def normalize_sql(sql: str) -> str:
    """Rewrite bare slash and dot table references to quoted slash form.

    - ``FROM fred/gdp``  becomes ``FROM "fred/gdp"``
    - ``FROM fred.gdp``  becomes ``FROM "fred/gdp"``
    - Already-quoted refs like ``FROM "fred/gdp"`` are left untouched.
    """
    # Unquoted slash form: FROM fred/gdp -> FROM "fred/gdp"
    result = re.sub(
        r'(\b(?:FROM|JOIN)\s+)(?!")([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)(?!")',
        r'\1"\2/\3"',
        sql,
        flags=re.IGNORECASE,
    )
    # Dot form: FROM fred.gdp -> FROM "fred/gdp"
    result = re.sub(
        r'(\b(?:FROM|JOIN)\s+)(?!")([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)(?!")',
        r'\1"\2/\3"',
        result,
        flags=re.IGNORECASE,
    )
    return result
