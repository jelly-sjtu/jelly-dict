"""Kokoro local TTS provider.

Apache-2.0 model + MIT-licensed Python wrapper. No credit obligation.
Requires the optional dependency group: see requirements-tts.txt.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

from app.anki.tts.base import ProviderInfo, TTSResult

logger = logging.getLogger(__name__)


# Kokoro v1.0+ ships voices for both English and Japanese. The lists below
# are what the settings UI will offer; the underlying library may support
# more, but we expose a curated set to keep the picker manageable.
VOICES_EN: tuple[str, ...] = (
    "af_heart",
    "af_bella",
    "af_nicole",
    "am_adam",
    "am_michael",
    "bf_emma",
)
VOICES_JA: tuple[str, ...] = (
    "jf_alpha",
    "jf_gongitsune",
    "jm_kumo",
)


class KokoroProvider:
    @classmethod
    def info(cls) -> ProviderInfo:
        return ProviderInfo(
            id="kokoro",
            display_name="Kokoro (로컬)",
            available=cls.is_available(),
            voices_en=VOICES_EN,
            voices_ja=VOICES_JA,
            requires_credit=False,
            license_note="Apache-2.0 / MIT — 자유 사용 가능",
            usage_warning="",
        )

    @classmethod
    def is_available(cls) -> bool:
        # Cheap check — DO NOT actually `import kokoro` here, that pulls
        # torch/scipy and takes 3–5 seconds on first call, blocking the
        # UI when the settings dialog rebuilds the engine combos.
        import importlib.util

        return (
            importlib.util.find_spec("kokoro") is not None
            and importlib.util.find_spec("soundfile") is not None
        )

    def __init__(self, settings) -> None:
        self._settings = settings
        self._pipeline_en = None
        self._pipeline_ja = None

    def _pipeline_for(self, language: str):
        from kokoro import KPipeline  # type: ignore

        if language == "ja":
            if self._pipeline_ja is None:
                try:
                    self._pipeline_ja = KPipeline(lang_code="j")
                except ModuleNotFoundError as exc:
                    if "pyopenjtalk" in str(exc) or "misaki" in str(exc):
                        raise RuntimeError(
                            "일본어 음소 모듈이 누락됐습니다. 설정의 Kokoro 🗑로 "
                            "한 번 삭제 후 다시 설치하거나 "
                            "`pip install 'misaki[ja]'`을 실행하세요."
                        ) from exc
                    raise
                except RuntimeError as exc:
                    msg = str(exc)
                    if (
                        "MeCab" in msg
                        or "mecabrc" in msg
                        or "dicdir" in msg
                        or "unidic" in msg
                    ):
                        raise RuntimeError(
                            "일본어 형태소 사전(unidic)이 다운로드되지 않았습니다. "
                            "설정의 Kokoro 🗑로 삭제 후 다시 설치하거나, "
                            "터미널에서 `python -m unidic download`를 실행하세요."
                        ) from exc
                    raise
            return self._pipeline_ja
        if self._pipeline_en is None:
            self._pipeline_en = KPipeline(lang_code="a")
        return self._pipeline_en

    def synthesize(
        self,
        text: str,
        *,
        language: str,
        voice: str,
        out_path: Path,
    ) -> TTSResult:
        import soundfile as sf  # type: ignore

        pipeline = self._pipeline_for(language)
        # KPipeline yields (graphemes, phonemes, audio) per chunk.
        chunks: list = []
        for _g, _p, audio in pipeline(text, voice=voice):
            chunks.append(audio)
        if not chunks:
            raise RuntimeError("Kokoro produced no audio")

        # Concatenate if multiple chunks.
        if len(chunks) == 1:
            audio = chunks[0]
        else:
            import numpy as np  # type: ignore

            audio = np.concatenate(chunks)

        # Kokoro samples at 24kHz. Write WAV first, then ffmpeg → mp3.
        wav_path = out_path.with_suffix(".wav")
        sf.write(str(wav_path), audio, 24000)
        _wav_to_mp3(wav_path, out_path, self._settings)

        return TTSResult(
            path=out_path,
            engine_id="kokoro",
            voice=voice,
            requires_credit=False,
            credit_text="",
            license_note="Kokoro (Apache-2.0)",
        )


def _wav_to_mp3(wav: Path, mp3: Path, settings) -> None:
    """Transcode WAV to mono mp3 using ffmpeg, falling back to keeping WAV."""
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found; keeping WAV at %s (larger file size)", wav)
        # Rename so the cache path still resolves; caller treats the
        # resulting file as the audio asset regardless of extension.
        try:
            mp3.unlink(missing_ok=True)
        except OSError:
            pass
        wav.replace(mp3)
        return
    bitrate = getattr(settings, "tts_bitrate", "96k")
    sr = getattr(settings, "tts_sample_rate", 44100)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(wav),
        "-ac", "1",
        "-ar", str(sr),
        "-b:a", bitrate,
        str(mp3),
    ]
    try:
        subprocess.run(cmd, check=True)
    finally:
        try:
            wav.unlink()
        except OSError:
            pass
