import pytest
from datetime import datetime, timedelta
from ai_tools_core.usage.trackers import NoOpUsageTracker, InMemoryUsageTracker
from ai_tools_core.usage.events import UsageEvent

def test_noop_tracker_track_usage(sample_usage_event):
    tracker = NoOpUsageTracker()
    tracker.track_usage(sample_usage_event)
    stats = tracker.get_current_usage()
    assert stats["total_tokens"] == 0
    assert stats["event_count"] == 0

class TestInMemoryUsageTracker:
    def test_track_single_event(self, sample_usage_event):
        tracker = InMemoryUsageTracker()
        tracker.track_usage(sample_usage_event)
        
        stats = tracker.get_current_usage()
        assert stats["total_input_tokens"] == 10
        assert stats["total_output_tokens"] == 20
        assert stats["total_tokens"] == 30
        assert stats["event_count"] == 1
        
    def test_filter_by_user_id(self, sample_usage_event):
        tracker = InMemoryUsageTracker()
        tracker.track_usage(sample_usage_event)
        
        other_event = UsageEvent(
            model="gpt-4o-mini",
            input_tokens=5,
            output_tokens=5,
            request_type="chat",
            user_id="other_user",
            session_id="test_session"
        )
        tracker.track_usage(other_event)
        
        stats = tracker.get_current_usage(user_id="test_user")
        assert stats["total_tokens"] == 30
        assert stats["event_count"] == 1
        
    def test_filter_by_time_range(self, sample_usage_event):
        pytest.skip("Timestamp filtering not implemented in base class")
        
    def test_model_breakdown(self, sample_usage_event):
        tracker = InMemoryUsageTracker()
        tracker.track_usage(sample_usage_event)
        
        stats = tracker.get_current_usage()
        assert "model_breakdown" in stats
        assert "gpt-4o-mini" in stats["model_breakdown"]
        assert stats["model_breakdown"]["gpt-4o-mini"]["total_tokens"] == 30
