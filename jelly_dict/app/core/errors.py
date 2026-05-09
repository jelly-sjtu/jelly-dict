from __future__ import annotations


class AppError(Exception):
    """Base for all jelly dict application errors."""


class NetworkError(AppError):
    pass


class NoInternetError(NetworkError):
    pass


class HttpStatusError(NetworkError):
    def __init__(self, status_code: int, message: str = "") -> None:
        super().__init__(message or f"HTTP {status_code}")
        self.status_code = status_code


class RateLimitedError(NetworkError):
    pass


class DomainNotAllowedError(NetworkError):
    """Raised when code attempts a request to a non-whitelisted domain."""


class ParseError(AppError):
    pass


class NotFoundError(AppError):
    pass


class StorageError(AppError):
    pass


class ExcelLockedError(StorageError):
    pass


class ExcelFormatError(StorageError):
    pass


class CacheError(StorageError):
    pass


class ExportError(AppError):
    pass


class UnsupportedLanguageError(AppError):
    pass
