import json
from pathlib import Path
from typing import List, Dict, Any
from src.datalake import (
    write_channel_messages_json,
    write_manifest,
    telegram_messages_partition_dir,
)


def test_write_channel_messages_json(tmp_path: Path) -> None:
    """
    Test that `write_channel_messages_json` correctly writes messages to a JSON file.

    Steps:
    1. Writes a list of messages to a JSON file.
    2. Checks that the output file exists.
    3. Verifies that the content matches the input messages.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.
    """
    base_path: Path = tmp_path
    date_str: str = "2026-01-18"
    channel_name: str = "testchannel"

    messages: List[Dict[str, Any]] = [
        {
            "message_id": 1,
            "channel_name": channel_name,
            "message_text": "Hello world",
            "views": 10,
        }
    ]

    out_path: str = write_channel_messages_json(
        base_path=str(base_path),
        date_str=date_str,
        channel_name=channel_name,
        messages=messages,
    )

    # File exists
    assert Path(out_path).exists()

    # Content is correct
    with open(out_path, "r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = json.load(f)

    assert data == messages


def test_write_manifest(tmp_path: Path) -> None:
    """
    Test that `write_manifest` correctly writes a manifest JSON file.

    Steps:
    1. Writes a manifest with per-channel message counts.
    2. Checks that the output file exists.
    3. Verifies that the date, channel counts, and total message count are correct.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.
    """
    base_path: Path = tmp_path
    date_str: str = "2026-01-18"

    channel_counts: Dict[str, int] = {
        "cheMed123": 10,
        "tikvahpharma": 5,
    }

    out_path: str = write_manifest(
        base_path=str(base_path),
        date_str=date_str,
        channel_message_counts=channel_counts,
    )

    assert Path(out_path).exists()

    with open(out_path, "r", encoding="utf-8") as f:
        manifest: Dict[str, Any] = json.load(f)

    assert manifest["date"] == date_str
    assert manifest["channels"] == channel_counts
    assert manifest["total_messages"] == sum(channel_counts.values())


def test_partition_directory_created(tmp_path: Path) -> None:
    """
    Test that the partition directory for Telegram messages is created correctly.

    Steps:
    1. Generates the partition directory path using `telegram_messages_partition_dir`.
    2. Ensures that the directory path ends with the expected date string.

    Args:
        tmp_path (Path): Temporary directory provided by pytest.
    """
    date_str: str = "2026-01-18"

    partition_dir: str = telegram_messages_partition_dir(
        base_path=str(tmp_path),
        date_str=date_str,
    )

    assert partition_dir.endswith(date_str)
