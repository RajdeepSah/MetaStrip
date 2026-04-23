import os


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # 25 MB upload limit
    MAX_CONTENT_LENGTH: int = 25 * 1024 * 1024

    CORS_ORIGINS: list[str] = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000"
    ).split(",")

    ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/heic",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    )

    # TTL cache: max 100 cleaned files, each held 15 minutes
    CACHE_MAX_SIZE: int = 100
    CACHE_TTL_SECONDS: int = 900
