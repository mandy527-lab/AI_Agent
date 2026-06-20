import json

from src.history import (
    analysis_from_entry,
    create_history_entry,
    delete_history_entry,
    load_history,
    save_analysis,
)
from tests.test_agent import sample_analysis


def test_save_and_load_history_without_raw_inputs(tmp_path):
    path = tmp_path / "history.json"
    result = sample_analysis()

    entry = save_analysis(result, used_resume=True, path=path)
    history = load_history(path)

    assert len(history) == 1
    assert history[0]["id"] == entry["id"]
    assert history[0]["used_resume"] is True
    assert "resume_text" not in history[0]
    assert "job_descriptions" not in history[0]
    assert analysis_from_entry(history[0]) == result


def test_create_history_entry_is_safe_for_session_storage():
    entry = create_history_entry(sample_analysis(), used_resume=True)

    assert entry["used_resume"] is True
    assert "resume_text" not in entry
    assert "job_descriptions" not in entry


def test_delete_history_entry(tmp_path):
    path = tmp_path / "history.json"
    first = save_analysis(sample_analysis(), used_resume=False, path=path)
    second = save_analysis(sample_analysis(), used_resume=False, path=path)

    delete_history_entry(first["id"], path=path)
    remaining = load_history(path)

    assert [item["id"] for item in remaining] == [second["id"]]


def test_invalid_history_file_returns_empty_list(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("{broken", encoding="utf-8")

    assert load_history(path) == []


def test_history_is_limited_to_max_entries(tmp_path):
    path = tmp_path / "history.json"
    for _ in range(3):
        save_analysis(sample_analysis(), used_resume=False, path=path, max_entries=2)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 2
