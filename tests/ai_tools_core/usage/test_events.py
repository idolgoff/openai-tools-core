from datetime import datetime
import pytest
from ai_tools_core.usage.events import UsageEvent


def test_usage_event_required_params():
    event = UsageEvent(
        model="gpt-4o-mini",
        input_tokens=10,
        output_tokens=20,
        request_type="chat",
    )
    assert event.model == "gpt-4o-mini"
    assert event.input_tokens == 10
    assert event.output_tokens == 20
    assert event.request_type == "chat"
    assert event.total_tokens == 30
    assert event.user_id is None
    assert event.session_id is None
    assert event.metadata == {}


def test_usage_event_optional_params():
    metadata = {"temperature": 0.7}
    event = UsageEvent(
        model="gpt-4o-mini",
        input_tokens=10,
        output_tokens=20,
        request_type="chat",
        user_id="test_user",
        session_id="test_session",
        metadata=metadata,
    )
    assert event.user_id == "test_user"
    assert event.session_id == "test_session"
    assert event.metadata == metadata


def test_usage_event_timestamp_generation():
    before = datetime.now().isoformat()
    event = UsageEvent(
        model="gpt-4o-mini",
        input_tokens=10,
        output_tokens=20,
        request_type="chat",
    )
    after = datetime.now().isoformat()
    assert before <= event.timestamp <= after


def test_usage_event_to_dict():
    metadata = {"temperature": 0.7}
    event = UsageEvent(
        model="gpt-4o-mini",
        input_tokens=10,
        output_tokens=20,
        request_type="chat",
        user_id="test_user",
        session_id="test_session",
        metadata=metadata,
    )
    
    event_dict = event.to_dict()
    assert event_dict["model"] == "gpt-4o-mini"
    assert event_dict["input_tokens"] == 10
    assert event_dict["output_tokens"] == 20
    assert event_dict["total_tokens"] == 30
    assert event_dict["request_type"] == "chat"
    assert event_dict["user_id"] == "test_user"
    assert event_dict["session_id"] == "test_session"
    assert event_dict["metadata"] == metadata
    assert "timestamp" in event_dict
