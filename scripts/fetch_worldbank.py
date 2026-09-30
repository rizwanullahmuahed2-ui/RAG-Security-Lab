"""Fetch a pinned, auditable Afghanistan WDI snapshot (no credentials needed).

Run from the project root: python scripts/fetch_worldbank.py
Existing snapshots are preserved; pass --refresh explicitly to replace them.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
INDICATORS = {
    "SP.POP.TOTL": "Demography",
    "SP.URB.TOTL.IN.ZS": "Demography",
    "SP.DYN.LE00.IN": "Health",
    "SP.DYN.TFRT.IN": "Health",
    "SP.DYN.IMRT.IN": "Health",
    "NY.GDP.MKTP.CD": "Economy",
    "NY.GDP.PCAP.CD": "Economy",
    "IT.NET.USER.ZS": "Technology",
    "IT.CEL.SETS.P2": "Technology",
    "EG.ELC.ACCS.ZS": "Infrastructure",
    "AG.LND.AGRI.ZS": "Environment",
    "AG.LND.FRST.ZS": "Environment",
}


def fetch(code: str, refresh: bool = False) -> dict:
    destination = ROOT / "data" / "sources" / "worldbank" / f"{code}.json"
    if destination.exists() and not refresh:
        return json.loads(destination.read_text(encoding="utf-8"))
    url = (f"https://api.worldbank.org/v2/country/AFG/indicator/{code}"
           "?date=2010:2023&format=json&per_page=1000&source=2")
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                body = response.read()
            payload = json.loads(body)
            if not isinstance(payload, list) or len(payload) != 2 or not payload[1]:
                raise ValueError(f"Unexpected World Bank response for {code}")
            if int(payload[0]["pages"]) != 1:
                raise ValueError("Pagination required; refusing a partial snapshot")
            snapshot = {
                "url": url, "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "response_sha256": hashlib.sha256(body).hexdigest(),
                "response_body": body.decode("utf-8"),
                "category": INDICATORS[code], "payload": payload,
            }
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
            return snapshot
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda code: fetch(code, args.refresh), INDICATORS))
    print(f"Saved {len(results)} source snapshots; "
          f"{sum(sum(r['value'] is not None for r in s['payload'][1]) for s in results)} non-null observations.")
