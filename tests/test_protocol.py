# tests/test_protocol.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from protocol.framing import create_packet, unpack_packet, HEADER_SIZE
from protocol.serializer import encode, decode
from protocol.protocol import make_message
from protocol.message_types import MessageType
from protocol.validator import validate


def test_make_message():
    """Test message creation."""
    msg = make_message(MessageType.PLAYER_READY, 1, player_id="player_1", deck_list=[])
    assert msg["type"] == "PLAYER_READY"
    assert msg["seq_num"] == 1
    assert msg["player_id"] == "player_1"
    assert msg["deck_list"] == []
    print("✅ make_message works")


def test_validate():
    """Test message validation."""
    msg = make_message(MessageType.PLAYER_READY, 1, player_id="player_1")
    validate(msg)  # Should not raise
    print("✅ validate works")


def test_validate_missing_type():
    """Test validation with missing type."""
    msg = {"seq_num": 1}
    with pytest.raises(ValueError, match="Missing 'type' field"):
        validate(msg)
    print("✅ Missing type detected")


def test_validate_missing_seq_num():
    """Test validation with missing seq_num."""
    msg = {"type": "PLAYER_READY"}
    with pytest.raises(ValueError, match="Missing 'seq_num' field"):
        validate(msg)
    print("✅ Missing seq_num detected")


def test_serializer():
    """Test JSON serialization."""
    msg = {"type": "TEST", "seq_num": 1}
    encoded = encode(msg)
    assert isinstance(encoded, bytes)
    decoded = decode(encoded)
    assert decoded == msg
    print("✅ Serializer works")


def test_framing():
    """Test packet framing."""
    msg = {"type": "TEST", "seq_num": 1}
    packet = create_packet(msg)
    assert len(packet) >= HEADER_SIZE
    unpacked = unpack_packet(packet)
    assert unpacked == msg
    print("✅ Framing works")


def test_all_message_types():
    """Test all message types."""
    for msg_type in MessageType:
        msg = make_message(msg_type, 1)
        validate(msg)
        packet = create_packet(msg)
        unpacked = unpack_packet(packet)
        assert unpacked["type"] == msg_type.value
    print(f"✅ All {len(MessageType)} message types work")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("TESTING PROTOCOL")
    print("="*60)
    
    test_make_message()
    test_validate()
    test_validate_missing_type()
    test_validate_missing_seq_num()
    test_serializer()
    test_framing()
    test_all_message_types()
    
    print("\n" + "="*60)
    print("✅ ALL PROTOCOL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()