from django.db.models import Q
from django.core.cache import cache
from django.utils import timezone

REPAIR_STATUS_KEY = "ohlcv_repair:status"
REPAIR_LOCK_KEY = "ohlcv_repair:lock"
REPAIR_LOCK_TTL = 6 * 3600
REPAIR_LOG_LIMIT = 50


def _default_status() -> dict:
    now = timezone.now().isoformat()
    return {
        "state": "idle",
        "source": None,
        "initiated_by": None,
        "symbol": None,
        "date_from": None,
        "date_to": None,
        "total_assets": 0,
        "processed_assets_count": 0,
        "invalid_rows_found": 0,
        "invalid_rows_deleted": 0,
        "repaired_rows": 0,
        "current_asset": None,
        "processed_assets": [],
        "started_at": None,
        "updated_at": now,
        "completed_at": None,
    }


def get_repair_status() -> dict:
    return cache.get(REPAIR_STATUS_KEY) or _default_status()


def save_repair_status(status: dict) -> dict:
    status["updated_at"] = timezone.now().isoformat()
    cache.set(REPAIR_STATUS_KEY, status, REPAIR_LOCK_TTL)
    return status


def start_repair_status(
    *,
    total_assets: int,
    source: str,
    initiated_by: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    status = _default_status()
    status.update({
        "state": "queued",
        "source": source,
        "initiated_by": initiated_by,
        "symbol": symbol,
        "date_from": date_from,
        "date_to": date_to,
        "total_assets": total_assets,
        "started_at": timezone.now().isoformat(),
    })
    return save_repair_status(status)


def set_repair_lock() -> bool:
    return cache.add(REPAIR_LOCK_KEY, "1", timeout=REPAIR_LOCK_TTL)


def clear_repair_lock() -> None:
    cache.delete(REPAIR_LOCK_KEY)


def update_repair_status(**updates) -> dict:
    status = get_repair_status()
    status.update(updates)
    return save_repair_status(status)


def _append_processed_asset(status: dict, entry: dict) -> dict:
    processed_assets = list(status.get("processed_assets", []))
    processed_assets.append(entry)
    status["processed_assets"] = processed_assets[-REPAIR_LOG_LIMIT:]
    status["processed_assets_count"] = int(status.get("processed_assets_count", 0)) + 1
    return status


def mark_repair_asset_started(*, symbol: str, index: int, total_assets: int) -> dict:
    status = get_repair_status()
    status["state"] = "running"
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_repair_status(status)


def mark_repair_asset_completed(
    *,
    symbol: str,
    invalid_rows_deleted: int,
    rows_ingested: int,
    index: int,
    total_assets: int,
) -> dict:
    status = get_repair_status()
    status = _append_processed_asset(status, {
        "symbol": symbol,
        "status": "completed",
        "invalid_rows_deleted": invalid_rows_deleted,
        "rows_ingested": rows_ingested,
        "timestamp": timezone.now().isoformat(),
    })
    status["invalid_rows_found"] = int(status.get("invalid_rows_found", 0)) + invalid_rows_deleted
    status["invalid_rows_deleted"] = int(status.get("invalid_rows_deleted", 0)) + invalid_rows_deleted
    status["repaired_rows"] = int(status.get("repaired_rows", 0)) + rows_ingested
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_repair_status(status)


def mark_repair_asset_failed(*, symbol: str, error: str, index: int, total_assets: int) -> dict:
    status = get_repair_status()
    status = _append_processed_asset(status, {
        "symbol": symbol,
        "status": "failed",
        "error": error,
        "timestamp": timezone.now().isoformat(),
    })
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_repair_status(status)


def finish_repair_status(*, state: str = "completed") -> dict:
    status = get_repair_status()
    status["state"] = state
    status["current_asset"] = None
    status["completed_at"] = timezone.now().isoformat()
    return save_repair_status(status)


def queue_ohlcv_repair(
    *,
    source: str,
    initiated_by: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[bool, dict]:
    from markets.models import Asset
    from markets.tasks import repair_ohlcv_history

    queryset = Asset.objects.filter(ohlcv_data__isnull=False)
    if symbol:
        queryset = queryset.filter(Q(display_symbol__iexact=symbol) | Q(provider_symbol__iexact=symbol))
    total_assets = queryset.distinct().count()
    if not set_repair_lock():
        return False, get_repair_status()

    status = start_repair_status(
        total_assets=total_assets,
        source=source,
        initiated_by=initiated_by,
        symbol=symbol,
        date_from=date_from,
        date_to=date_to,
    )
    repair_ohlcv_history.delay(
        source=source,
        initiated_by=initiated_by,
        symbol=symbol,
        date_from=date_from,
        date_to=date_to,
    )
    return True, status
