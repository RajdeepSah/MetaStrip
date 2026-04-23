"""Image metadata extraction and stripping engine.

Supported formats: JPEG, PNG, TIFF, HEIC/HEIF.

Uses piexif for structured EXIF parsing (GPS, camera tags, timestamps)
and Pillow for format-agnostic I/O and clean re-encoding.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

import piexif
from PIL import Image, ExifTags

try:
    from pillow_heif import register_heif_opener  # type: ignore[import]

    register_heif_opener()
    _HEIC_SUPPORTED = True
except ImportError:
    _HEIC_SUPPORTED = False

from .base import BaseEngine
from ..utils.scoring import compute_sensitivity


# ── MIME map ──────────────────────────────────────────────────────────────────

_FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "TIFF": "image/tiff",
    "HEIF": "image/heic",
    "HEIC": "image/heic",
}


def _format_to_mime(fmt: str) -> str:
    return _FORMAT_TO_MIME.get(fmt.upper(), f"image/{fmt.lower()}")


# ── Empty findings skeleton ───────────────────────────────────────────────────

def _empty_findings() -> dict[str, Any]:
    return {
        "gps": None,
        "camera": {},
        "timestamps": {},
        "author": None,
        "thumbnail_embedded": False,
        "raw_exif": {},
    }


# ── GPS helpers ───────────────────────────────────────────────────────────────

def _rational(val: tuple[int, int]) -> float:
    num, den = val
    return num / den if den != 0 else 0.0


def _dms_to_decimal(
    dms: list[tuple[int, int]], ref: bytes | str
) -> float:
    """Convert EXIF DMS triplet to signed decimal degrees."""
    deg = _rational(dms[0])
    mn = _rational(dms[1]) / 60.0
    sec = _rational(dms[2]) / 3600.0
    result = deg + mn + sec
    if ref in (b"S", b"W", "S", "W"):
        result = -result
    return round(result, 7)


def _parse_gps(gps_ifd: dict) -> dict[str, float] | None:
    """Return {lat, lon, altitude?} or None if GPS data is absent/malformed."""
    if not gps_ifd:
        return None
    try:
        lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
        lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)
        lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)

        if not all([lat_ref, lat, lon_ref, lon]):
            return None

        gps: dict[str, float] = {
            "lat": _dms_to_decimal(lat, lat_ref),
            "lon": _dms_to_decimal(lon, lon_ref),
        }

        alt = gps_ifd.get(piexif.GPSIFD.GPSAltitude)
        if alt:
            altitude = _rational(alt)
            if gps_ifd.get(piexif.GPSIFD.GPSAltitudeRef) == 1:
                altitude = -altitude
            gps["altitude"] = round(altitude, 1)

        return gps
    except (KeyError, ZeroDivisionError, TypeError, IndexError):
        return None


# ── Raw EXIF serialiser ───────────────────────────────────────────────────────

def _decode_value(val: Any) -> Any:
    """Convert a piexif value into a JSON-serialisable form."""
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace").strip("\x00")
    if isinstance(val, tuple) and len(val) == 2 and all(isinstance(v, int) for v in val):
        # Single rational number
        return _rational(val)
    if isinstance(val, (list, tuple)):
        decoded = [_decode_value(v) for v in val]
        return decoded[0] if len(decoded) == 1 else decoded
    return val


def _decode_ifd(ifd: dict) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for tag_id, value in ifd.items():
        name = ExifTags.TAGS.get(tag_id, f"tag_{tag_id}")
        result[name] = _decode_value(value)
    return result


# ── Format-specific extractors ────────────────────────────────────────────────

def _extract_exif(file_bytes: bytes) -> dict[str, Any]:
    """Parse EXIF from JPEG/TIFF/HEIF bytes via piexif."""
    findings = _empty_findings()

    try:
        exif_data = piexif.load(file_bytes)
    except Exception:
        return findings

    zeroth = exif_data.get("0th") or {}
    exif_ifd = exif_data.get("Exif") or {}
    gps_ifd = exif_data.get("GPS") or {}

    # Camera / device
    def _str(tag: int, ifd: dict = zeroth) -> str:
        raw = ifd.get(tag, b"")
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace").strip("\x00 ")
        return str(raw)

    make = _str(piexif.ImageIFD.Make)
    model = _str(piexif.ImageIFD.Model)
    software = _str(piexif.ImageIFD.Software)

    if any([make, model, software]):
        findings["camera"] = {
            k: v
            for k, v in {"make": make, "model": model, "software": software}.items()
            if v
        }

    # Timestamps
    taken = _str(piexif.ExifIFD.DateTimeOriginal, exif_ifd)
    digitized = _str(piexif.ExifIFD.DateTimeDigitized, exif_ifd)
    modified = _str(piexif.ImageIFD.DateTime)
    ts = {k: v for k, v in {
        "taken": taken,
        "digitized": digitized,
        "modified": modified,
    }.items() if v}
    if ts:
        findings["timestamps"] = ts

    # Author
    artist = _str(piexif.ImageIFD.Artist)
    if artist:
        findings["author"] = artist

    # GPS
    findings["gps"] = _parse_gps(gps_ifd)

    # Embedded thumbnail (stored in IFD1 + 'thumbnail' key)
    findings["thumbnail_embedded"] = bool(exif_data.get("thumbnail"))

    # Raw dump (0th + Exif IFDs; GPS already shown separately)
    raw: dict[str, Any] = {}
    raw.update(_decode_ifd(zeroth))
    raw.update(_decode_ifd(exif_ifd))
    findings["raw_exif"] = raw

    return findings


def _extract_png(img: Image.Image) -> dict[str, Any]:
    """Extract tEXt / iTXt / eXIf chunks from a PNG image."""
    findings = _empty_findings()

    # Modern PNG: embedded EXIF via eXIf chunk
    exif_bytes: bytes | None = img.info.get("exif")  # type: ignore[assignment]
    if exif_bytes:
        try:
            return _extract_exif(exif_bytes)
        except Exception:
            pass

    # Legacy tEXt / iTXt / zTXt text metadata
    raw: dict[str, Any] = {}
    for key, value in img.info.items():
        if key in ("exif", "icc_profile", "transparency", "background"):
            continue
        if isinstance(value, str):
            raw[str(key)] = value
        elif hasattr(value, "text"):
            raw[str(key)] = str(value.text)

    if raw:
        findings["raw_exif"] = raw
        author = raw.get("Author") or raw.get("author") or raw.get("Creator")
        if author:
            findings["author"] = author

    return findings


# ── Engine class ──────────────────────────────────────────────────────────────

class ImageEngine(BaseEngine):
    """Handles JPEG, PNG, TIFF, and HEIC metadata extraction and stripping."""

    def extract(self, file_bytes: bytes) -> dict:
        """Return structured metadata findings. Never raises — errors go into the dict."""
        try:
            return self._extract(file_bytes)
        except Exception as exc:
            return {
                "file_type": "image/unknown",
                "findings": _empty_findings(),
                "sensitivity_score": 0,
                "risks": [],
                "error": str(exc),
            }

    def _extract(self, file_bytes: bytes) -> dict:
        img = Image.open(BytesIO(file_bytes))
        fmt = (img.format or "").upper()
        file_type = _format_to_mime(fmt)

        if fmt in ("JPEG", "TIFF", "HEIF", "HEIC"):
            findings = _extract_exif(file_bytes)
        elif fmt == "PNG":
            findings = _extract_png(img)
        else:
            findings = _empty_findings()

        score, risks = compute_sensitivity(findings)
        return {
            "file_type": file_type,
            "findings": findings,
            "sensitivity_score": score,
            "risks": risks,
        }

    def strip(self, file_bytes: bytes) -> bytes:
        """Return image bytes with all EXIF / metadata removed."""
        img = Image.open(BytesIO(file_bytes))
        fmt = (img.format or "JPEG").upper()
        output = BytesIO()

        if fmt in ("JPEG", "HEIF", "HEIC"):
            # Convert to RGB (HEIC may be other modes; JPEG can't store alpha)
            rgb = img.convert("RGB")
            # exif=b"" is the most reliable way to produce a metadata-free JPEG
            rgb.save(output, format="JPEG", exif=b"", quality=95, optimize=True)

        elif fmt == "PNG":
            # Re-save without pnginfo — Pillow does not carry tEXt chunks forward
            # unless you explicitly pass pnginfo=.  exif=b"" drops any eXIf chunk.
            img.save(output, format="PNG", exif=b"")

        elif fmt == "TIFF":
            # Save fresh, then use piexif.remove for a belt-and-suspenders strip
            img.save(output, format="TIFF")
            try:
                return piexif.remove(output.getvalue())
            except Exception:
                pass  # already saved without exif argument; return as-is

        else:
            img.save(output, format=fmt)

        return output.getvalue()
