from .headers import SecurityHeadersDetector
from .html import HtmlSurfaceDetector
from .javascript import JavaScriptDetector
from .source_map import SourceMapDetector


def default_detectors():
    return (
        SecurityHeadersDetector(),
        HtmlSurfaceDetector(),
        JavaScriptDetector(),
        SourceMapDetector(),
    )


__all__ = [
    "HtmlSurfaceDetector",
    "JavaScriptDetector",
    "SecurityHeadersDetector",
    "SourceMapDetector",
    "default_detectors",
]
