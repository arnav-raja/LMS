"""Turning report rows into a CSV file a browser will download.

Every report in the admin area is something a compliance or HR person
eventually needs outside the application — in a spreadsheet, in an email,
attached to an audit. Reading it off the screen and retyping it is the
alternative this replaces.
"""

import csv
import io
from datetime import datetime

from fastapi.responses import StreamingResponse


def _format(value) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        # Excel reads TRUE/FALSE; "True" it leaves as text.
        return "TRUE" if value else "FALSE"

    if isinstance(value, datetime):
        # ISO 8601, so a spreadsheet sorts it correctly and a human can
        # still read it. Timestamps are timezone-aware since Phase 2.
        return value.isoformat()

    return str(value)


def csv_response(
    filename: str,
    headers: list[str],
    rows: list[list],
) -> StreamingResponse:
    """A downloadable CSV.

    Written with the `csv` module rather than by joining commas, because
    course titles and people's names contain commas and quotes, and doing
    it by hand silently corrupts exactly the rows that matter most.

    The BOM is deliberate: without it Excel on Windows reads UTF-8 as the
    system codepage and mangles every non-ASCII name in the file.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")

    writer.writerow(headers)
    for row in rows:
        writer.writerow([_format(value) for value in row])

    content = "﻿" + buffer.getvalue()

    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename(filename)}"'
        },
    )


def safe_filename(name: str) -> str:
    """A filename that cannot break out of the Content-Disposition header.

    The name is built from a course or quiz title, which an admin types,
    so it can contain quotes, newlines, semicolons — anything. Rather than
    escaping, this keeps only characters that are unambiguous in a header
    and on every filesystem.

    ASCII only, and that part is not cosmetic: header values are encoded
    as latin-1, so a title containing a character outside it — a Polish ł,
    anything CJK — would raise while building the response rather than
    downloading with an odd name. The file's *contents* are UTF-8 and keep
    every character; only the filename is reduced.
    """
    kept = [
        character
        if (character.isascii() and (character.isalnum() or character in "-_. "))
        else "-"
        for character in name
    ]

    cleaned = "".join(kept).strip().strip(".") or "export"

    return cleaned[:100]
