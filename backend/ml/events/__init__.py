"""Video event recording for model training."""


from .video_events import VideoEventRecorder, EventType, setup_event_schema, normalize_id

 

__all__ = ['VideoEventRecorder', 'EventType', 'setup_event_schema', 'normalize_id']