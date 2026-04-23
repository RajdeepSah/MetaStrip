"""Unit tests for image_engine.py.

All fixture images are generated programmatically in conftest.py —
no external files are needed to run this suite.
"""
from __future__ import annotations

from io import BytesIO

import piexif
import pytest
from PIL import Image

from app.engines.image_engine import ImageEngine


# ── Extraction: GPS ───────────────────────────────────────────────────────────

def test_gps_coordinates_extracted(jpeg_with_gps: bytes) -> None:
    result = ImageEngine().extract(jpeg_with_gps)
    gps = result["findings"]["gps"]
    assert gps is not None, "GPS should be present"
    # 37°46'29.6"N ≈ 37.7749
    assert abs(gps["lat"] - 37.7749) < 0.01
    # 122°25'9.8"W ≈ -122.4194
    assert abs(gps["lon"] - (-122.4194)) < 0.01
    assert gps.get("altitude") == 52.0


def test_no_gps_returns_none(jpeg_no_exif: bytes) -> None:
    result = ImageEngine().extract(jpeg_no_exif)
    assert result["findings"]["gps"] is None


# ── Extraction: camera + author ───────────────────────────────────────────────

def test_camera_info_extracted(jpeg_with_gps: bytes) -> None:
    result = ImageEngine().extract(jpeg_with_gps)
    camera = result["findings"]["camera"]
    assert camera.get("make") == "Apple"
    assert "iPhone" in camera.get("model", "")
    assert camera.get("software") == "17.4.1"


def test_author_extracted(jpeg_with_gps: bytes) -> None:
    result = ImageEngine().extract(jpeg_with_gps)
    assert result["findings"]["author"] == "Jane Doe"


def test_timestamps_extracted(jpeg_with_gps: bytes) -> None:
    result = ImageEngine().extract(jpeg_with_gps)
    ts = result["findings"]["timestamps"]
    assert ts.get("taken") == "2023:08:15 10:30:00"


# ── Sensitivity scoring ───────────────────────────────────────────────────────

def test_gps_drives_high_score(jpeg_with_gps: bytes) -> None:
    result = ImageEngine().extract(jpeg_with_gps)
    assert result["sensitivity_score"] >= 50
    assert len(result["risks"]) >= 1
    assert any("GPS" in r or "location" in r.lower() for r in result["risks"])


def test_no_metadata_gives_low_score(jpeg_no_exif: bytes) -> None:
    result = ImageEngine().extract(jpeg_no_exif)
    assert result["sensitivity_score"] < 30


def test_camera_without_gps_intermediate_score(jpeg_no_gps_but_camera: bytes) -> None:
    result = ImageEngine().extract(jpeg_no_gps_but_camera)
    # Camera info adds points but no GPS, so score should be moderate
    score = result["sensitivity_score"]
    assert 5 <= score < 50


# ── Strip ─────────────────────────────────────────────────────────────────────

def test_strip_produces_valid_jpeg(jpeg_with_gps: bytes) -> None:
    stripped = ImageEngine().strip(jpeg_with_gps)
    img = Image.open(BytesIO(stripped))
    assert img.format == "JPEG"


def test_strip_removes_gps(jpeg_with_gps: bytes) -> None:
    stripped = ImageEngine().strip(jpeg_with_gps)
    result = ImageEngine().extract(stripped)
    assert result["findings"]["gps"] is None


def test_strip_removes_camera_info(jpeg_with_gps: bytes) -> None:
    stripped = ImageEngine().strip(jpeg_with_gps)
    result = ImageEngine().extract(stripped)
    assert result["findings"]["camera"] == {}


def test_strip_removes_author(jpeg_with_gps: bytes) -> None:
    stripped = ImageEngine().strip(jpeg_with_gps)
    result = ImageEngine().extract(stripped)
    assert result["findings"]["author"] is None


# ── PNG ───────────────────────────────────────────────────────────────────────

def test_png_text_chunks_extracted(png_with_text: bytes) -> None:
    result = ImageEngine().extract(png_with_text)
    assert result["file_type"] == "image/png"
    raw = result["findings"]["raw_exif"]
    assert "Author" in raw or "author" in raw


def test_png_author_promoted_to_top_level(png_with_text: bytes) -> None:
    result = ImageEngine().extract(png_with_text)
    assert result["findings"]["author"] == "Bob Smith"


def test_png_strip_removes_text_chunks(png_with_text: bytes) -> None:
    stripped = ImageEngine().strip(png_with_text)
    result = ImageEngine().extract(stripped)
    assert result["findings"]["author"] is None
    assert result["findings"]["raw_exif"] == {}


# ── Error resilience ──────────────────────────────────────────────────────────

def test_corrupt_file_does_not_raise(corrupt_bytes: bytes) -> None:
    result = ImageEngine().extract(corrupt_bytes)
    # Must return a dict, never propagate an exception
    assert isinstance(result, dict)
    assert "error" in result or result["findings"]["gps"] is None


# ── Response structure ────────────────────────────────────────────────────────

def test_result_has_required_keys(jpeg_no_exif: bytes) -> None:
    result = ImageEngine().extract(jpeg_no_exif)
    for key in ("file_type", "findings", "sensitivity_score", "risks"):
        assert key in result, f"Missing key: {key}"
    findings = result["findings"]
    for key in ("gps", "camera", "timestamps", "author", "thumbnail_embedded", "raw_exif"):
        assert key in findings, f"Missing findings key: {key}"
    assert isinstance(result["sensitivity_score"], int)
    assert 0 <= result["sensitivity_score"] <= 100
    assert isinstance(result["risks"], list)
