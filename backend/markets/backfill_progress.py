from django.core.cache import cache
from django.utils import timezone

BACKFILL_STATUS_KEY = "ohlcv_backfill:status"
BACKFILL_LOCK_KEY = "ohlcv_backfill:lock"
BACKFILL_LOCK_TTL = 6 * 3600
BACKFILL_LOG_LIMIT = 50


def _default_status() -> dict:
    now = timezone.now().isoformat()
    return {
        "state": "idle",
        "source": None,
        "initiated_by": None,
        "total_assets": 0,
        "processed_assets_count": 0,
        "successful_assets": 0,
        "failed_assets": 0,
        "current_asset": None,
        "processed_assets": [],
        "started_at": None,
        "updated_at": now,
        "completed_at": None,
    }


def get_backfill_status() -> dict:
    return cache.get(BACKFILL_STATUS_KEY) or _default_status()


def save_backfill_status(status: dict) -> dict:
    status["updated_at"] = timezone.now().isoformat()
    cache.set(BACKFILL_STATUS_KEY, status, BACKFILL_LOCK_TTL)
    return status


def start_backfill_status(*, total_assets: int, source: str, initiated_by: str | None = None) -> dict:
    status = _default_status()
    status.update({
        "state": "queued",
        "source": source,
        "initiated_by": initiated_by,
        "total_assets": total_assets,
        "started_at": timezone.now().isoformat(),
    })
    return save_backfill_status(status)


def set_backfill_lock() -> bool:
    return cache.add(BACKFILL_LOCK_KEY, "1", timeout=BACKFILL_LOCK_TTL)


def clear_backfill_lock() -> None:
    cache.delete(BACKFILL_LOCK_KEY)


def update_backfill_status(**updates) -> dict:
    status = get_backfill_status()
    status.update(updates)
    return save_backfill_status(status)


def _append_processed_asset(status: dict, entry: dict) -> dict:
    processed_assets = list(status.get("processed_assets", []))
    processed_assets.append(entry)
    status["processed_assets"] = processed_assets[-BACKFILL_LOG_LIMIT:]
    status["processed_assets_count"] = int(status.get("processed_assets_count", 0)) + 1
    return status


def mark_backfill_asset_started(*, symbol: str, index: int, total_assets: int) -> dict:
    status = get_backfill_status()
    status["state"] = "running"
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_backfill_status(status)


def mark_backfill_asset_completed(*, symbol: str, rows_ingested: int, index: int, total_assets: int) -> dict:
    status = get_backfill_status()
    status = _append_processed_asset(status, {
        "symbol": symbol,
        "status": "completed",
        "rows_ingested": rows_ingested,
        "timestamp": timezone.now().isoformat(),
    })
    status["successful_assets"] = int(status.get("successful_assets", 0)) + 1
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_backfill_status(status)


def mark_backfill_asset_failed(*, symbol: str, error: str, index: int, total_assets: int) -> dict:
    status = get_backfill_status()
    status = _append_processed_asset(status, {
        "symbol": symbol,
        "status": "failed",
        "error": error,
        "timestamp": timezone.now().isoformat(),
    })
    status["failed_assets"] = int(status.get("failed_assets", 0)) + 1
    status["current_asset"] = {
        "symbol": symbol,
        "index": index,
        "total_assets": total_assets,
    }
    return save_backfill_status(status)


def finish_backfill_status(*, state: str = "completed") -> dict:
    status = get_backfill_status()
    status["state"] = state
    status["current_asset"] = None
    status["completed_at"] = timezone.now().isoformat()
    return save_backfill_status(status)


def queue_ohlcv_backfill(*, source: str, initiated_by: str | None = None) -> tuple[bool, dict]:
    from markets.models import Asset
    from markets.tasks import backfill_ohlcv_historical

    total_assets = Asset.objects.filter(is_seeded=True).count()
    if not set_backfill_lock():
        return False, get_backfill_status()

    status = start_backfill_status(
        total_assets=total_assets,
        source=source,
        initiated_by=initiated_by,
    )
    backfill_ohlcv_historical.delay(source=source, initiated_by=initiated_by)
    return True, status
