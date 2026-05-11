from __future__ import annotations

from typing import Optional

from app.ocr.apple_vision import AppleVisionOcrProvider
from app.ocr.base import OcrProvider


def build_ocr_provider(name: str | None, settings=None) -> OcrProvider:
    provider = (name or "apple_vision").strip().lower()
    if provider == "apple_vision":
        return AppleVisionOcrProvider()
    if provider == "google_vision":
        from app.ocr.google_vision import GoogleVisionOcrProvider
        from app.storage import secret_store

        key = secret_store.get("google_vision_api_key")
        if not key:
            raise RuntimeError(
                "Google Vision OCR을 사용하려면 설정에서 API 키를 입력하세요."
            )
        endpoint = (
            settings.google_vision_endpoint
            if settings is not None
            else "https://vision.googleapis.com/v1/images:annotate"
        )
        return GoogleVisionOcrProvider(key, endpoint)
    raise ValueError(f"지원하지 않는 OCR provider: {provider}")
