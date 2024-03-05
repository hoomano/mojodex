import pytest

from core import providers

def test_core_providers_does_not_exist():
    obj = providers
    with pytest.raises(Exception) as e:
        obj.first("fake-model")

def test_core_providers_first():
    # providers.available should not be empty
    obj = providers
    assert obj.available

def test_core_providers_gpt4_mandatory():
    # gpt4-turbo should be in providers.available
    obj = providers
    assert obj.first("gpt-4-turbo")

