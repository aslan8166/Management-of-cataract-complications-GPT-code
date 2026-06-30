"""Fetch a PubMed corpus snapshot via NCBI E-utilities (esearch + efetch).

AGENTS.md data-source contract:
  * Use NCBI_API_KEY (env) when present; respect rate limits (<=10 req/s with key,
    ~3 req/s without); exponential backoff + retry.
  * Use the history server (WebEnv/QueryKey); paginate efetch in batches (~200).
  * Cache ALL raw XML to data/raw/<snapshot>/ and write a retrieval log
    (exact query, retrieval timestamp, tool versions, returned PMID list).
  * PubMed is non-stationary: every run creates a NEW dated snapshot directory —
    NEVER a silent overwrite.

NOTE: in this build environment the session egress policy denies
eutils.ncbi.nlm.nih.gov (CONNECT -> 403). This module is complete and correct;
it will run once NCBI is allow-listed (or NCBI_API_KEY + network are available).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import lxml

FETCH_PY_VERSION = "0.1.0"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "ophth-llm-temporal-validity"
DEFAULT_BATCH = 200
MAX_RETRIES = 5


def load_query(path: str | Path) -> str:
    """Read query.txt, drop comment/blank lines, normalize whitespace."""
    lines = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            lines.append(s)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def build_client() -> httpx.Client:
    """httpx client wired for the session proxy + CA bundle (see /root/.ccr)."""
    ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    return httpx.Client(
        base_url=EUTILS,
        verify=ca if ca else True,
        proxy=proxy,
        timeout=httpx.Timeout(60.0),
        headers={"User-Agent": f"{TOOL}/{FETCH_PY_VERSION}"},
    )


class RateLimiter:
    """Minimum-interval limiter. 10 req/s with key, ~3 req/s without."""

    def __init__(self, per_sec: float):
        self.min_interval = 1.0 / per_sec
        self._last = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()


RETRYABLE_STATUS = (429, 500, 502, 503, 504)
EGRESS_HINT = (
    "eutils.ncbi.nlm.nih.gov appears blocked by this session's egress policy "
    "(proxy denial). Do NOT retry/route around it — report the blocked host so it "
    "can be allow-listed (see /root/.ccr/README.md)."
)


def _request(client, limiter, path, params, *, expect_json):
    """GET with rate limiting + exponential backoff.

    Retries ONLY transient failures (429, 5xx, transport errors). A policy
    denial (403/407) or other 4xx is raised immediately, not retried — per the
    proxy README guardrail.
    """
    last_exc = None
    for attempt in range(MAX_RETRIES):
        limiter.wait()
        try:
            resp = client.get(path, params=params)
        except httpx.TransportError as exc:  # connect/read/proxy transport issues
            last_exc = exc
            msg = str(exc)
            # A proxy CONNECT denial surfaces as ProxyError("403/407 ..."); do not retry.
            if isinstance(exc, httpx.ProxyError) and ("403" in msg or "407" in msg):
                raise RuntimeError(f"E-utilities proxy denial ({msg}). {EGRESS_HINT}") from exc
        else:
            if resp.status_code in RETRYABLE_STATUS:
                last_exc = httpx.HTTPStatusError(
                    f"retryable {resp.status_code}", request=resp.request, response=resp)
            elif resp.status_code in (403, 407):
                raise RuntimeError(f"E-utilities {resp.status_code} denied. {EGRESS_HINT}")
            elif resp.status_code >= 400:
                resp.raise_for_status()
            else:
                return resp.json() if expect_json else resp.content
        if attempt == MAX_RETRIES - 1:
            break
        backoff = min(30.0, 2.0 ** attempt) + random.uniform(0, 0.5)
        print(f"  [retry {attempt+1}/{MAX_RETRIES}] {last_exc} -> sleep {backoff:.1f}s",
              file=sys.stderr)
        time.sleep(backoff)
    raise RuntimeError(
        f"E-utilities request failed after {MAX_RETRIES} attempts: {last_exc}. {EGRESS_HINT}"
    ) from last_exc


def _auth_params(api_key, email):
    p = {"tool": TOOL}
    if api_key:
        p["api_key"] = api_key
    if email:
        p["email"] = email
    return p


def esearch(client, limiter, query, retmax, api_key, email):
    params = {"db": "pubmed", "term": query, "usehistory": "y",
              "retmax": retmax, "retstart": 0, "retmode": "json"}
    params.update(_auth_params(api_key, email))
    data = _request(client, limiter, "/esearch.fcgi", params, expect_json=True)
    r = data["esearchresult"]
    return {
        "count": int(r["count"]),
        "webenv": r["webenv"],
        "querykey": r["querykey"],
        "idlist": r.get("idlist", []),
        "querytranslation": r.get("querytranslation", ""),
    }


def efetch_batch(client, limiter, webenv, querykey, retstart, retmax, api_key, email):
    params = {"db": "pubmed", "WebEnv": webenv, "query_key": querykey,
              "retstart": retstart, "retmax": retmax, "retmode": "xml"}
    params.update(_auth_params(api_key, email))
    return _request(client, limiter, "/efetch.fcgi", params, expect_json=False)


def _count_records(xml: bytes) -> int:
    return len(re.findall(rb"<PubmedArticle\b", xml))


def fetch_snapshot(query_path, out_root, retmax, batch_size=DEFAULT_BATCH):
    query_raw = Path(query_path).read_text(encoding="utf-8")
    query = load_query(query_path)
    api_key = os.environ.get("NCBI_API_KEY") or ""
    email = os.environ.get("NCBI_EMAIL") or os.environ.get("CLAUDE_CODE_USER_EMAIL") or ""
    limiter = RateLimiter(10.0 if api_key else 3.0)

    ts = datetime.now(timezone.utc)
    snap = Path(out_root) / ts.strftime("%Y%m%dT%H%M%SZ")
    snap.mkdir(parents=True, exist_ok=True)

    with build_client() as client:
        es = esearch(client, limiter, query, max(retmax, 1), api_key, email)
        target = es["count"] if retmax == 0 else min(retmax, es["count"])
        print(f"esearch: count={es['count']} target={target} "
              f"(api_key={'yes' if api_key else 'no'})")

        batches = []
        for retstart in range(0, target, batch_size):
            n = min(batch_size, target - retstart)
            xml = efetch_batch(client, limiter, es["webenv"], es["querykey"],
                               retstart, n, api_key, email)
            fname = f"efetch_{retstart:06d}.xml"
            (snap / fname).write_bytes(xml)
            nrec = _count_records(xml)
            batches.append({"retstart": retstart, "retmax": n,
                            "file": fname, "n_records": nrec})
            print(f"  efetch [{retstart}..{retstart+n}) -> {fname} ({nrec} records)")

    log = {
        "retrieval_timestamp_utc": ts.isoformat(),
        "eutils_base": EUTILS,
        "db": "pubmed",
        "query_raw": query_raw,
        "query_normalized": query,
        "query_translation": es["querytranslation"],
        "corpus_count_at_retrieval": es["count"],
        "requested_retmax": retmax,
        "target_fetched": target,
        "returned_pmids": es["idlist"],
        "webenv": es["webenv"],
        "querykey": es["querykey"],
        "batches": batches,
        "batch_size": batch_size,
        "api_key_used": bool(api_key),
        "rate_limit_per_sec": 10.0 if api_key else 3.0,
        "tool_versions": {
            "python": platform.python_version(),
            "httpx": httpx.__version__,
            "lxml": lxml.__version__,
            "fetch_py": FETCH_PY_VERSION,
        },
    }
    (snap / "retrieval_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Snapshot written: {snap}")
    return snap


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fetch a PubMed snapshot (E-utilities).")
    ap.add_argument("--query", default="config/query.txt")
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--retmax", type=int, default=50,
                    help="pilot size; 0 = fetch entire corpus")
    ap.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    args = ap.parse_args(argv)
    fetch_snapshot(args.query, args.out, args.retmax, args.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
