"""Programmatic test fixtures — no external files needed.

All fixture images are generated in memory using Pillow + piexif so
the test suite is fully self-contained.
"""
from __future__ import annotations

from io import BytesIO

import piexif
import pytest
from PIL import Image, PngImagePlugin


# ── GPS helper ────────────────────────────────────────────────────────────────

def _dms(degrees: int, minutes: int, seconds_tenths: int) -> list[tuple[int, int]]:
    """Return DMS as piexif rational triples.  seconds_tenths is seconds × 10."""
    return [(degrees, 1), (minutes, 1), (seconds_tenths, 10)]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def jpeg_with_gps() -> bytes:
    """100×100 JPEG carrying GPS coords (San Francisco), camera info, and author."""
    img = Image.new("RGB", (100, 100), (73, 109, 137))

    exif_dict: dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Apple",
            piexif.ImageIFD.Model: b"iPhone 14 Pro",
            piexif.ImageIFD.Software: b"17.4.1",
            piexif.ImageIFD.Artist: b"Jane Doe",
            piexif.ImageIFD.DateTime: b"2023:08:15 10:30:00",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2023:08:15 10:30:00",
            piexif.ExifIFD.DateTimeDigitized: b"2023:08:15 10:30:01",
        },
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: _dms(37, 46, 296),   # 37°46'29.6"N
            piexif.GPSIFD.GPSLongitudeRef: b"W",
            piexif.GPSIFD.GPSLongitude: _dms(122, 25, 98),  # 122°25'9.8"W
            piexif.GPSIFD.GPSAltitudeRef: 0,
            piexif.GPSIFD.GPSAltitude: (52, 1),
        },
        "1st": {},
    }
    exif_bytes = piexif.dump(exif_dict)

    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()


@pytest.fixture(scope="session")
def jpeg_no_exif() -> bytes:
    """Plain 100×100 JPEG with no EXIF data at all."""
    img = Image.new("RGB", (100, 100), (200, 200, 200))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def jpeg_no_gps_but_camera() -> bytes:
    """JPEG with camera metadata but no GPS."""
    img = Image.new("RGB", (80, 80), (50, 80, 120))
    exif_dict: dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Canon",
            piexif.ImageIFD.Model: b"EOS R5",
            piexif.ImageIFD.Software: b"Firmware 1.8.0",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2024:01:20 14:00:00",
        },
        "GPS": {},
    }
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=piexif.dump(exif_dict))
    return buf.getvalue()


@pytest.fixture(scope="session")
def png_with_text() -> bytes:
    """PNG carrying tEXt metadata chunks (Author, Software, Comment)."""
    img = Image.new("RGB", (60, 60), (200, 100, 50))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Author", "Bob Smith")
    meta.add_text("Software", "GIMP 2.10.36")
    meta.add_text("Comment", "Test fixture — do not distribute")
    buf = BytesIO()
    img.save(buf, format="PNG", pnginfo=meta)
    return buf.getvalue()


@pytest.fixture(scope="session")
def corrupt_bytes() -> bytes:
    """Bytes that start like a JPEG but are otherwise garbage."""
    return b"\xff\xd8\xff\xe0" + b"\x00" * 16 + b"not valid jpeg content at all"
