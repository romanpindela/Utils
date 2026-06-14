"""
Module for converting audio files to different formats
and checking for ffmpeg binary, and downloading it if not found.
"""

import os
import platform
import re
import shlex
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

from spotdl.utils.config import get_spotdl_path
from spotdl.utils.formatter import to_ms

__all__ = [
    "FFMPEG_URLS",
    "FFMPEG_FORMATS",
    "DUR_REGEX",
    "TIME_REGEX",
    "VERSION_REGEX",
    "YEAR_REGEX",
    "FFmpegError",
    "is_ffmpeg_installed",
    "get_ffmpeg_path",
    "get_ffmpeg_version",
    "get_local_ffmpeg",
    "download_ffmpeg",
    "convert",
]

FFMPEG_URLS = {
    "windows": {
        "amd64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/win32-x64",
        "i686": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/win32-ia32",
    },
    "linux": {
        "x86_64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/linux-x64",
        "x86": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/linux-ia32",
        "arm32": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/linux-arm",
        "aarch64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/linux-arm64",
    },
    "darwin": {
        "x86_64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/darwin-x64",
        "arm64": "https://github.com/eugeneware/ffmpeg-static/releases/download/b4.4/darwin-arm64",
    },
}

FFMPEG_FORMATS = {
    "mp3": ["-codec:a", "libmp3lame"],
    "flac": ["-codec:a", "flac", "-sample_fmt", "s16"],
    "ogg": ["-codec:a", "libvorbis"],
    "opus": ["-codec:a", "libopus"],
    "m4a": ["-codec:a", "aac"],
    "wav": ["-codec:a", "pcm_s16le"],
}

DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)
TIME_REGEX = re.compile(
    r"out_time=(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)
VERSION_REGEX = re.compile(r"ffmpeg version \w?(\d+\.)?(\d+)")
YEAR_REGEX = re.compile(r"Copyright \(c\) \d\d\d\d\-\d\d\d\d")


class FFmpegError(Exception):
    """
    Base class for all exceptions related to FFmpeg.
    """


def is_ffmpeg_installed(ffmpeg: str = "ffmpeg") -> bool:
    if ffmpeg == "ffmpeg":
        global_ffmpeg = shutil.which("ffmpeg")
        if global_ffmpeg is None:
            ffmpeg_path = get_ffmpeg_path()
        else:
            ffmpeg_path = Path(global_ffmpeg)
    else:
        ffmpeg_path = Path(ffmpeg)

    if ffmpeg_path is None:
        return False

    return ffmpeg_path.exists() and os.access(ffmpeg_path, os.X_OK)


def get_ffmpeg_path() -> Optional[Path]:
    global_ffmpeg = shutil.which("ffmpeg")
    if global_ffmpeg:
        return Path(global_ffmpeg)
    return get_local_ffmpeg()


def get_ffmpeg_version(ffmpeg: str = "ffmpeg") -> Tuple[Optional[float], Optional[int]]:
    if not is_ffmpeg_installed(ffmpeg):
        raise FFmpegError(f"{ffmpeg} is not a valid ffmpeg executable.")

    with subprocess.Popen(
        [ffmpeg, "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    ) as process:
        output = "".join(process.communicate())

    version_result = VERSION_REGEX.search(output)
    year_result = YEAR_REGEX.search(output)

    version = float(re.sub(r"[a-zA-Z]", "", version_result.group(0))) if version_result else None
    build_year = max([
        int(re.sub(r"[^0-9]", "", year))
        for year in year_result.group(0).split("-")
    ]) if year_result else None

    return version, build_year


def get_local_ffmpeg() -> Optional[Path]:
    ffmpeg_path = Path(get_spotdl_path()) / ("ffmpeg" + (".exe" if platform.system() == "Windows" else ""))
    return ffmpeg_path if ffmpeg_path.is_file() else None


def download_ffmpeg() -> Path:
    os_name = platform.system().lower()
    os_arch = platform.machine().lower()
    ffmpeg_url = FFMPEG_URLS.get(os_name, {}).get(os_arch)

    if ffmpeg_url is None:
        raise FFmpegError("FFmpeg binary is not available for your system.")

    ffmpeg_path = Path(get_spotdl_path()) / ("ffmpeg" + (".exe" if os_name == "windows" else ""))
    ffmpeg_binary = requests.get(ffmpeg_url, allow_redirects=True, timeout=10).content

    with open(ffmpeg_path, "wb") as ffmpeg_file:
        ffmpeg_file.write(ffmpeg_binary)

    if os_name in ["linux", "darwin"]:
        ffmpeg_path.chmod(ffmpeg_path.stat().st_mode | stat.S_IEXEC)

    return ffmpeg_path


def convert(
    input_file: Union[Path, Tuple[str, str]],
    output_file: Path,
    ffmpeg: str = "ffmpeg",
    output_format: str = "mp3",
    bitrate: Optional[str] = None,
    ffmpeg_args: Optional[str] = None,
    progress_handler: Optional[Callable[[int], None]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    arguments: List[str] = [
        "-nostdin", "-y", "-i",
        str(input_file.resolve()) if isinstance(input_file, Path) else input_file[0],
        "-movflags", "+faststart", "-v", "debug",
        "-progress", "-", "-nostats"
    ]

    file_format = (
        str(input_file.suffix).split(".")[1]
        if isinstance(input_file, Path)
        else input_file[1]
    )

    if output_format == "opus" and file_format != "webm":
        arguments.extend(["-c:a", "libopus"])
    else:
        if (
            (output_format == "opus" and file_format == "webm")
            or (output_format == "m4a" and file_format == "m4a")
            and not (bitrate or ffmpeg_args)
        ):
            arguments.extend(["-vn", "-c:a", "copy"])
        else:
            arguments.extend(FFMPEG_FORMATS[output_format])

    if bitrate:
        if bitrate.lower() == "copy":
            raise FFmpegError('Nieprawidłowa wartość bitrate: "copy". Użyj "-c:a copy" zamiast przekazywania tego jako bitrate.')
        elif bitrate.isdigit():
            arguments.extend(["-q:a", bitrate])
        else:
            arguments.extend(["-b:a", bitrate])

    if ffmpeg_args:
        arguments.extend(shlex.split(ffmpeg_args))

    arguments.append(str(output_file.resolve()))

    with subprocess.Popen(
        [ffmpeg, *arguments],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=False,
    ) as process:
        if not progress_handler:
            proc_out = process.communicate()

            if process.returncode != 0:
                version = get_ffmpeg_version(ffmpeg)
                message = b"".join([out for out in proc_out if out]).decode("utf-8")
                return False, {
                    "return_code": process.returncode,
                    "arguments": arguments,
                    "ffmpeg": ffmpeg,
                    "version": version[0],
                    "build_year": version[1],
                    "error": message,
                }
            return True, None

        progress_handler(0)

        out_buffer = []
        total_dur = None
        while True:
            if process.stdout is None:
                continue

            out_line = (
                process.stdout.readline().decode("utf-8", errors="replace").strip()
            )

            if out_line == "" and process.poll() is not None:
                break

            out_buffer.append(out_line.strip())

            total_dur_match = DUR_REGEX.search(out_line)
            if total_dur is None and total_dur_match:
                total_dur = to_ms(**total_dur_match.groupdict())
                continue
            if total_dur:
                progress_time = TIME_REGEX.search(out_line)
                if progress_time:
                    elapsed_time = to_ms(**progress_time.groupdict())
                    progress_handler(int(elapsed_time / total_dur * 100))

        if process.returncode != 0:
            version = get_ffmpeg_version(ffmpeg)
            return False, {
                "return_code": process.returncode,
                "arguments": arguments,
                "ffmpeg": ffmpeg,
                "version": version[0],
                "build_year": version[1],
                "error": "\n".join(out_buffer),
            }

        progress_handler(100)
        return True, None
