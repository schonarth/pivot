import re
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field


MAX_REQUEST_STATS = 100
MAX_FINGERPRINTS_PER_REQUEST = 20


_number_pattern = re.compile(r"\b\d+(?:\.\d+)?\b")
_quoted_pattern = re.compile(r"'(?:''|[^'])*'")
_whitespace_pattern = re.compile(r"\s+")
_lock = threading.Lock()
_requests = deque(maxlen=MAX_REQUEST_STATS)
_total_requests = 0
_total_queries = 0


@dataclass
class QueryCapture:
    queries: list[dict[str, object]] = field(default_factory=list)

    def __call__(self, execute, sql, params, many, context):
        started_at = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            self.queries.append(
                {
                    "fingerprint": normalize_sql(sql),
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
            )


def normalize_sql(sql: str) -> str:
    normalized = _quoted_pattern.sub("?", sql)
    normalized = _number_pattern.sub("?", normalized)
    normalized = _whitespace_pattern.sub(" ", normalized).strip()
    return normalized


def record_request_stat(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    queries: list[dict[str, object]],
) -> None:
    global _total_requests, _total_queries

    fingerprints = defaultdict(lambda: {"count": 0, "total_ms": 0.0})
    for query in queries:
        fingerprint = query["fingerprint"]
        fingerprints[fingerprint]["count"] += 1
        fingerprints[fingerprint]["total_ms"] += query["duration_ms"]

    top_fingerprints = sorted(
        (
            {
                "sql": sql,
                "count": data["count"],
                "total_ms": round(data["total_ms"], 3),
            }
            for sql, data in fingerprints.items()
        ),
        key=lambda item: (item["count"], item["total_ms"]),
        reverse=True,
    )[:MAX_FINGERPRINTS_PER_REQUEST]

    stat = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 3),
        "query_count": len(queries),
        "query_time_ms": round(sum(query["duration_ms"] for query in queries), 3),
        "fingerprints": top_fingerprints,
    }

    with _lock:
        _requests.appendleft(stat)
        _total_requests += 1
        _total_queries += len(queries)


def get_query_stats() -> dict[str, object]:
    with _lock:
        requests = list(_requests)
        heavy_paths = Counter()
        for request in requests:
            heavy_paths[request["path"]] += request["query_count"]

        return {
            "total_requests": _total_requests,
            "total_queries": _total_queries,
            "retained_requests": len(requests),
            "max_retained_requests": MAX_REQUEST_STATS,
            "heavy_paths": [
                {"path": path, "query_count": query_count}
                for path, query_count in heavy_paths.most_common(10)
            ],
            "requests": requests,
        }


def clear_query_stats() -> None:
    global _total_requests, _total_queries

    with _lock:
        _requests.clear()
        _total_requests = 0
        _total_queries = 0
