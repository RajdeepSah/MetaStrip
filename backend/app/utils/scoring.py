"""Sensitivity scoring heuristic.

Produces a 0-100 score and a human-readable risk list from a findings dict.
Higher score = more identifying information present.
"""


def compute_sensitivity(findings: dict) -> tuple[int, list[str]]:
    """Return (score, risks) for a findings dict."""
    score = 0
    risks: list[str] = []

    gps = findings.get("gps")
    if gps:
        score += 50
        risks.append(
            "Precise GPS location embedded — photo can be traced to a specific address"
        )

    camera = findings.get("camera") or {}
    make = camera.get("make", "")
    model = camera.get("model", "")
    if make or model:
        score += 10
        label = " ".join(filter(None, [make, model]))
        risks.append(f"Device fingerprint visible: {label}")

    software = camera.get("software", "")
    if software:
        score += 5
        risks.append(f"Editing/capture software version exposed: {software}")

    author = findings.get("author")
    if author:
        score += 15
        risks.append(f"Author identity embedded: \"{author}\"")

    if findings.get("thumbnail_embedded"):
        score += 10
        risks.append(
            "Embedded thumbnail may retain original framing/location "
            "even after the main image was edited or cropped"
        )

    raw = findings.get("raw_exif") or {}
    serial_keys = {
        "BodySerialNumber",
        "SerialNumber",
        "CameraSerialNumber",
        "LensSerialNumber",
        "InternalSerialNumber",
    }
    if serial_keys & set(raw.keys()):
        score += 15
        risks.append(
            "Camera or lens serial number present — can uniquely identify your device"
        )

    timestamps = findings.get("timestamps") or {}
    if timestamps.get("taken"):
        score += 5
        risks.append("Precise capture timestamp is embedded")

    return min(score, 100), risks
