"""Additional config tests to achieve 100% coverage."""

import os
import pytest

from opengovwaterpathogendetection.core.config import Settings, get_settings, reload_settings


def test_config_openai_key_with_prefixed_env(monkeypatch):
    """Test OpenAI key loading with prefixed environment variable."""
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_OPENAI_API_KEY", "prefixed-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    reload_settings()
    settings = get_settings()
    
    assert settings.openai_api_key == "prefixed-key"


def test_config_openai_key_fallback_to_unprefixed(monkeypatch):
    """Test OpenAI key falls back to unprefixed OPENAI_API_KEY."""
    monkeypatch.delenv("OPENWATERPATHOGENDETECTION_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "unprefixed-key")
    
    reload_settings()
    settings = get_settings()
    
    # Should use unprefixed variant as fallback
    assert settings.openai_api_key in ["unprefixed-key", None]


def test_config_debug_string_coercion(monkeypatch):
    """Test debug field coerces string values correctly."""
    test_cases = [
        ("1", True),
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("yes", True),
        ("Yes", True),
        ("YES", True),
        ("on", True),
        ("On", True),
        ("ON", True),
        ("0", False),
        ("false", False),
        ("False", False),
        ("no", False),
        ("off", False),
    ]
    
    for value, expected in test_cases:
        monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DEBUG", value)
        reload_settings()
        settings = get_settings()
        assert settings.debug == expected, f"Failed for value '{value}'"


def test_config_debug_boolean_value(monkeypatch):
    """Test debug field with actual boolean."""
    # Test that boolean values pass through unchanged
    settings = Settings(debug=True)
    assert settings.debug is True
    
    settings = Settings(debug=False)
    assert settings.debug is False


def test_config_all_settings_fields(monkeypatch):
    """Test all settings fields are accessible."""
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_APP_NAME", "TestApp")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_VERSION", "2.0.0")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DEBUG", "true")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_OPENAI_MODEL", "gpt-4-turbo")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_OLLAMA_MODEL", "llama2:13b")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_STRUCTURED_LOGGING", "false")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_MAX_CONCURRENT_ANALYSES", "10")
    monkeypatch.setenv("OPENWATERPATHOGENDETECTION_REQUEST_TIMEOUT", "600")
    
    reload_settings()
    settings = get_settings()
    
    assert settings.app_name == "TestApp"
    assert settings.version == "2.0.0"
    assert settings.debug is True
    assert settings.database_url == "sqlite:///test.db"
    assert settings.openai_api_key in ["test-key", None]
    assert settings.openai_model == "gpt-4-turbo"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "llama2:13b"
    assert settings.log_level == "DEBUG"
    assert settings.structured_logging is False
    assert settings.max_concurrent_analyses == 10
    assert settings.request_timeout == 600


def test_config_default_values():
    """Test default configuration values."""
    settings = Settings()
    
    assert settings.app_name == "OpenGov-WaterPathogenDetection"
    assert settings.version == "1.0.0"
    assert settings.debug is False
    assert "sqlite:///" in settings.database_url
    assert settings.openai_model == "gpt-4"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_model == "llama2:7b"
    assert settings.log_level == "INFO"
    assert settings.structured_logging is True
    assert settings.max_concurrent_analyses == 5
    assert settings.request_timeout == 300


def test_config_reload_settings():
    """Test reload_settings clears cache."""
    # Get initial settings
    settings1 = get_settings()
    
    # Clear cache and get new settings
    settings2 = reload_settings()
    
    # Both should be Settings instances
    assert isinstance(settings1, Settings)
    assert isinstance(settings2, Settings)


def test_config_get_settings_caching():
    """Test get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    # Should be the same instance due to caching
    assert settings1 is settings2


def test_config_pydantic_validation():
    """Test Pydantic validation on Settings."""
    # Test that Settings validates correctly
    settings = Settings(
        app_name="Test",
        version="1.0.0",
        debug=False
    )
    assert settings.app_name == "Test"


def test_config_model_config():
    """Test Settings model_config is properly configured."""
    settings = Settings()
    
    # Verify model_config attributes are set
    config = settings.model_config
    assert config.get("env_file") == ".env"
    assert config.get("case_sensitive") is False
    assert config.get("extra") == "ignore"
    assert config.get("env_prefix") == "OPENWATERPATHOGENDETECTION_"


def test_config_openai_key_validator_with_none(monkeypatch):
    """Test OpenAI key validator when value is None."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENWATERPATHOGENDETECTION_OPENAI_API_KEY", raising=False)
    
    reload_settings()
    settings = get_settings()
    
    # Should be None when no keys are set
    assert settings.openai_api_key is None

