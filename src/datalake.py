import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def ensure_dir(path: str) -> None:
    """
    Ensure that a directory exists at the specified path. Creates it if it doesn't exist.

    Args:
        path (str): The directory path to ensure exists.
    """
    os.makedirs(path, exist_ok=True)


def telegram_messages_partition_dir(base_path: str, date_str: str) -> str:
    """
    Get the path to the Telegram messages partition directory for a given date.

    Args:
        base_path (str): Base path of the data lake.
        date_str (str): Date string in 'YYYY-MM-DD' format.

    Returns:
        str: Full path to the partition directory for the date.
    """
    return os.path.join(base_path, "raw", "telegram_messages", date_str)


def telegram_images_dir(base_path: str) -> str:
    """
    Get the path to the Telegram images directory.

    Args:
        base_path (str): Base path of the data lake.

    Returns:
        str: Full path to the images directory.
    """
    return os.path.join(base_path, "raw", "images")


def channel_messages_json_path(base_path: str, date_str: str, channel_name: str) -> str:
    """
    Get the path for a channel's messages JSON file for a specific date.

    Ensures that the partition directory exists.

    Args:
        base_path (str): Base path of the data lake.
        date_str (str): Date string in 'YYYY-MM-DD' format.
        channel_name (str): Name of the Telegram channel.

    Returns:
        str: Full path to the channel's JSON file.
    """
    partition_dir = telegram_messages_partition_dir(base_path, date_str)
    ensure_dir(partition_dir)
    return os.path.join(partition_dir, f"{channel_name}.json")


def write_channel_messages_json(
    *,
    base_path: str,
    date_str: str,
    channel_name: str,
    messages: List[Dict[str, Any]],
) -> str:
    """
    Write messages for a (date, channel) partition to the raw data lake as a JSON file.

    Args:
        base_path (str): Base path of the data lake.
        date_str (str): Date string in 'YYYY-MM-DD' format.
        channel_name (str): Name of the Telegram channel.
        messages (List[Dict[str, Any]]): List of message dictionaries to write.

    Returns:
        str: Full path to the written JSON file.
    """
    out_path = channel_messages_json_path(base_path, date_str, channel_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    return out_path


def manifest_path(base_path: str, date_str: str) -> str:
    """
    Get the path to the manifest file for a given date.

    Ensures that the partition directory exists.

    Args:
        base_path (str): Base path of the data lake.
        date_str (str): Date string in 'YYYY-MM-DD' format.

    Returns:
        str: Full path to the manifest JSON file.
    """
    partition_dir = telegram_messages_partition_dir(base_path, date_str)
    ensure_dir(partition_dir)
    return os.path.join(partition_dir, "_manifest.json")


def write_manifest(
    *,
    base_path: str,
    date_str: str,
    channel_message_counts: Dict[str, int],
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Write a simple audit/metadata manifest file for the day's Telegram messages.

    Args:
        base_path (str): Base path of the data lake.
        date_str (str): Date string in 'YYYY-MM-DD' format.
        channel_message_counts (Dict[str, int]): Dictionary mapping channel names to message counts.
        extra (Optional[Dict[str, Any]]): Additional metadata to include in the manifest.

    Returns:
        str: Full path to the written manifest JSON file.
    """
    payload: Dict[str, Any] = {
        "date": date_str,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "channels": channel_message_counts,
        "total_messages": sum(channel_message_counts.values()),
    }
    if extra:
        payload.update(extra)

    out_path = manifest_path(base_path, date_str)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path
