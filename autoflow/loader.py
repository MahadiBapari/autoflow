"""Load CSV / Excel order files into a DataFrame.

All values are read as strings so that validation sees the raw input
before any type coercion happens.
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from autoflow.config import ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

Source = Union[str, Path, bytes]


class FileLoadError(Exception):
    """Raised when an input file cannot be read as tabular order data."""


def _extension(source: Source, filename: Optional[str]) -> str:
    name = filename if filename else (str(source) if not isinstance(source, bytes) else "")
    ext = Path(name).suffix.lower()
    if not ext:
        raise FileLoadError("Cannot determine file type: a filename with an extension is required.")
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileLoadError(f"Unsupported file type '{ext}'. Allowed types: {allowed}.")
    return ext


def load_file(source: Source, filename: Optional[str] = None) -> pd.DataFrame:
    """Read a CSV or Excel file from a path or raw bytes.

    Args:
        source: path to the file, or its raw bytes (e.g. from an upload).
        filename: original filename; required when ``source`` is bytes.

    Raises:
        FileLoadError: the file is missing, empty, unsupported or malformed.
    """
    ext = _extension(source, filename)

    if isinstance(source, bytes):
        data = source
    else:
        path = Path(source)
        if not path.is_file():
            raise FileLoadError(f"File not found: {path}")
        data = path.read_bytes()  # read-only access; the original is never modified

    if not data.strip():
        raise FileLoadError("The file is empty.")

    buffer = io.BytesIO(data)
    try:
        if ext == ".csv":
            df = _read_csv(buffer)
        else:
            engine = "openpyxl" if ext == ".xlsx" else None
            df = pd.read_excel(buffer, dtype=str, keep_default_na=False, engine=engine)
    except FileLoadError:
        raise
    except pd.errors.EmptyDataError:
        raise FileLoadError("The file contains no data.")
    except pd.errors.ParserError as exc:
        raise FileLoadError(f"The CSV file is malformed: {exc}")
    except (zipfile.BadZipFile, ValueError, KeyError, OSError, ImportError) as exc:
        raise FileLoadError(f"The Excel file could not be read (it may be corrupt): {exc}")

    df.columns = [str(c).strip().lower() for c in df.columns]
    if df.empty and len(df.columns) == 0:
        raise FileLoadError("The file contains no data.")

    logger.info("Loaded %d rows and %d columns", len(df), len(df.columns))
    return df


def _read_csv(buffer: io.BytesIO) -> pd.DataFrame:
    """Read CSV trying UTF-8 (with BOM support) first, then Latin-1."""
    for encoding in ("utf-8-sig", "latin-1"):
        buffer.seek(0)
        try:
            return pd.read_csv(
                buffer,
                dtype=str,
                keep_default_na=False,
                skipinitialspace=True,
                encoding=encoding,
            )
        except UnicodeDecodeError:
            continue
    raise FileLoadError("The CSV file encoding could not be decoded.")
