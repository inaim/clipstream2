"""
Workers package for Celery tasks.

Import submodules so Celery can resolve `workers.video_processor` when started
with `celery -A workers.video_processor worker`.
"""

from . import video_processor  # noqa: F401

__all__ = ["video_processor"]
