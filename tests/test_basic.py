#!/usr/bin/env python3
"""
Basic test to verify CI/CD setup is working.
"""


def test_basic_functionality():
    """Simple test to verify pytest is working"""
    assert True


def test_basic_math():
    """Test basic math operations"""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 20 / 4 == 5


def test_string_operations():
    """Test basic string operations"""
    assert "hello" + " " + "world" == "hello world"
    assert "python".upper() == "PYTHON"
    assert "TESTING".lower() == "testing"
    assert len("ci/cd") == 5