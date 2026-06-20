import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.models import MarketAnalysis


DEFAULT_HISTORY_PATH = Path(".job_market_history.json")


def load_history(path: Path = DEFAULT_HISTORY_PATH) -> list[dict[str, Any]]:
    """Load local analysis history, returning an empty list for missing data."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def save_analysis(
    result: MarketAnalysis,
    used_resume: bool,
    path: Path = DEFAULT_HISTORY_PATH,
    max_entries: int = 20,
) -> dict[str, Any]:
    """Save a privacy-conscious snapshot without raw jobs or resume text."""
    entry = create_history_entry(result, used_resume)
    history = load_history(path)
    history.insert(0, entry)
    path.write_text(
        json.dumps(history[:max_entries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return entry


def create_history_entry(
    result: MarketAnalysis,
    used_resume: bool,
) -> dict[str, Any]:
    """Create a history snapshot without writing it to shared storage."""
    return {
        "id": uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_role": result.target_role,
        "total_jobs": result.total_jobs,
        "used_resume": used_resume,
        "result": result.model_dump(mode="json"),
    }


def delete_history_entry(
    entry_id: str,
    path: Path = DEFAULT_HISTORY_PATH,
) -> None:
    history = [item for item in load_history(path) if item.get("id") != entry_id]
    path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def analysis_from_entry(entry: dict[str, Any]) -> MarketAnalysis:
    return MarketAnalysis.model_validate(entry["result"])
