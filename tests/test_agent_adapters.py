"""Tests for agent adapters."""

import pytest
from unittest.mock import Mock

from ethos_os.agents.adapters.base import (
    AgentAdapter,
    AdapterRegistry,
)
from ethos_os.agents.adapters.hermes import HermesAdapter
from ethos_os.agents.adapters.pi import PiAdapter
from ethos_os.agents.adapters.general import GeneralAgentAdapter


class TestAdapterRegistry:
    """Test AdapterRegistry."""

    def test_register_and_get(self):
        """Test registration and retrieval."""
        registry = AdapterRegistry()
        mock_adapter = Mock(spec=AgentAdapter)
        mock_adapter.adapter_type = "test"

        registry.register("test", mock_adapter)
        adapter = registry.get("test")
        assert adapter == mock_adapter

    def test_list_adapters(self):
        """Test listing adapters."""
        registry = AdapterRegistry()
        mock1 = Mock(spec=AgentAdapter)
        mock1.adapter_type = "test1"
        mock2 = Mock(spec=AgentAdapter)
        mock2.adapter_type = "test2"

        registry.register("test1", mock1)
        registry.register("test2", mock2)

        adapters = registry.list_adapters()
        assert "test1" in adapters
        assert "test2" in adapters


class TestHermesAdapter:
    """Test Hermes adapter."""

    def test_properties(self):
        """Test adapter properties."""
        adapter = HermesAdapter()
        assert adapter.adapter_type == "hermes"
        assert adapter.name == "Hermes"
        assert "Nous Research" in adapter.description

    def test_build_system_prompt(self):
        """Test system prompt building."""
        adapter = HermesAdapter()
        prompt = adapter.build_system_prompt()
        assert "Hermes" in prompt

    def test_build_system_prompt_with_context(self):
        """Test system prompt with context."""
        adapter = HermesAdapter()
        context = {"project": "Test Project", "task": "Implement feature"}
        prompt = adapter.build_system_prompt(context)
        assert "project" in prompt
        assert "Test Project" in prompt


class TestPiAdapter:
    """Test Pi adapter."""

    def test_properties(self):
        """Test adapter properties."""
        adapter = PiAdapter()
        assert adapter.adapter_type == "pi"
        assert adapter.name == "Pi"
        assert "empathetic" in adapter.description.lower()

    def test_build_system_prompt(self):
        """Test system prompt building."""
        adapter = PiAdapter()
        prompt = adapter.build_system_prompt()
        assert "Pi" in prompt
        assert "supportive" in prompt.lower()


class TestGeneralAgentAdapter:
    """Test General agent adapter."""

    def test_properties(self):
        """Test adapter properties."""
        adapter = GeneralAgentAdapter()
        assert adapter.adapter_type == "general"
        assert adapter.name == "General Agent"

    def test_build_system_prompt(self):
        """Test system prompt building."""
        adapter = GeneralAgentAdapter()
        prompt = adapter.build_system_prompt()
        assert "general-purpose" in prompt.lower() or "general agent" in prompt.lower() or "AI assistant" in prompt

    def test_build_system_prompt_with_context(self):
        """Test system prompt with context."""
        adapter = GeneralAgentAdapter()
        context = {"initiative": "Test Initiative"}
        prompt = adapter.build_system_prompt(context)
        assert "Initiative" in prompt


class TestFormatContext:
    """Test context formatting."""

    def test_single_key(self):
        """Test single key."""
        adapter = GeneralAgentAdapter()
        result = adapter._format_context({"key": "value"})
        assert "key: value" in result

    def test_multiple_keys(self):
        """Test multiple keys."""
        adapter = GeneralAgentAdapter()
        result = adapter._format_context({
            "key1": "value1",
            "key2": "value2",
        })
        assert "key1: value1" in result
        assert "key2: value2" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])