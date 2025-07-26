import math
import logging
from yt_dlp import YoutubeDL
from typing import Optional

# Set up logging for this module
logger = logging.getLogger(__name__)

# Global variable to store the downloaded file path, accessible within this module
_downloaded_file_path_global: Optional[str] = None

def parse_time_to_seconds(time_str: str) -> int:
    """Converts a 'HH:MM:SS' time string to seconds."""
    h, m, s = map(int, time_str.split(':'))
    return h * 3600 + m * 60 + s

def download_ranges_callback(info_dict: dict, ydl: YoutubeDL) -> list[dict]:
    """
    Callback for yt-dlp to specify download ranges based on start and end times
    provided in ydl.params.
    """
    start_time = ydl.params.get('start_time')
    end_time = ydl.params.get('end_time')
    
    if not start_time or not end_time:
        raise ValueError("start_time and end_time must be provided in ydl.params for download_ranges_callback.")

    start_seconds = parse_time_to_seconds(start_time)
    end_seconds = parse_time_to_seconds(end_time)
    return [{'start_time': start_seconds, 'end_time': end_seconds}]

def my_progress_hook(d: dict) -> None:
    """
    Progress hook for yt-dlp to capture the final downloaded filename.
    """
    global _downloaded_file_path_global
    if d['status'] == 'finished':
        _downloaded_file_path_global = d['filename']
        logger.info(f"Download finished. Final filename captured by hook: {_downloaded_file_path_global}")

def get_downloaded_filepath() -> Optional[str]:
    """
    Returns the path of the downloaded file, or None if not yet available.
    """
    return _downloaded_file_path_global
