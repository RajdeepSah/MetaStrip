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


def compute_sensitivity_pdf(findings: dict) -> tuple[int, list[str]]:
    """Return (score, risks) for a PDF findings dict."""
    score = 0
    risks: list[str] = []

    author = findings.get("author")
    if author:
        score += 25
        risks.append(f"Author identity embedded: \"{author}\"")

    creator_tool = findings.get("creator_tool")
    if creator_tool:
        score += 10
        risks.append(f"Creator application exposed: {creator_tool}")

    if findings.get("has_javascript"):
        score += 30
        risks.append("Document contains JavaScript — potential active content risk")

    if findings.get("has_incremental_updates"):
        score += 15
        risks.append(
            "Incremental update structure present — prior versions of content may be recoverable"
        )

    if findings.get("creation_date"):
        score += 10
        risks.append("Document creation timestamp is embedded")

    count = findings.get("embedded_file_count", 0)
    if count:
        score += 15
        risks.append(f"PDF contains {count} embedded file attachment(s)")

    if findings.get("form_fields"):
        score += 5
        risks.append("Form field names are present in document structure")

    return min(score, 100), risks


def compute_sensitivity_docx(findings: dict) -> tuple[int, list[str]]:
    """Return (score, risks) for a DOCX findings dict."""
    score = 0
    risks: list[str] = []

    author = findings.get("author")
    if author:
        score += 25
        risks.append(f"Author identity embedded: \"{author}\"")

    last_modified_by = findings.get("last_modified_by")
    if last_modified_by:
        score += 15
        risks.append(f"Last editor identity embedded: \"{last_modified_by}\"")

    company = findings.get("company")
    if company:
        score += 20
        risks.append(f"Organisation name embedded: \"{company}\"")

    tc = findings.get("tracked_changes_count", 0)
    if tc:
        score += 20
        risks.append(
            f"{tc} tracked change(s) present — original and revised text may both be recoverable"
        )

    cc = findings.get("comments_count", 0)
    if cc:
        score += 15
        risks.append(f"{cc} reviewer comment(s) embedded")

    revision = findings.get("revision")
    if revision is not None:
        try:
            if int(revision) > 1:
                score += 10
                risks.append(f"Revision counter is {revision} — document has been edited multiple times")
        except (ValueError, TypeError):
            pass

    app_name = findings.get("app_name")
    if app_name:
        score += 5
        risks.append(f"Authoring application exposed: {app_name}")

    return min(score, 100), risks
