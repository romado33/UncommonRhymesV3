import os
from typing import List, Dict
from openai import OpenAI

_client = None

def get_client() -> OpenAI:"""
LLM Provider Abstraction
=========================

Provides a unified interface for different LLM providers.
Supports: Anthropic (Claude), OpenAI (GPT), and future providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str, max_tokens: int = 500, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat completion request"""
        pass
    
    def complete_json(self, prompt: str, schema_hint: str = "", temperature: Optional[float] = None) -> Dict[str, Any]:
        """Complete with JSON output"""
        temp = temperature if temperature is not None else self.temperature
        
        json_prompt = f"{prompt}\n\nReturn ONLY valid JSON matching this schema: {schema_hint}"
        messages = [
            {"role": "system", "content": "You are a helpful assistant that returns valid JSON."},
            {"role": "user", "content": json_prompt}
        ]
        
        # Temporarily adjust temperature for JSON completion
        old_temp = self.temperature
        self.temperature = temp
        
        try:
            response = self.chat(messages)
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
        except json.JSONDecodeError:
            return {}
        finally:
            self.temperature = old_temp
    
    def complete_lines(self, prompt: str, n: int = 10) -> List[str]:
        """Complete with line-separated output"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Return results as a simple list, one per line."},
            {"role": "user", "content": f"{prompt}\n\nReturn exactly {n} results, one per line."}
        ]
        
        response = self.chat(messages)
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        return lines[:n]


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) provider"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        # Extract system message if present
        system_msg = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_msg if system_msg else anthropic.NOT_GIVEN,
            messages=user_messages
        )
        
        return response.content[0].text


class OpenAIProvider(LLMProvider):
    """OpenAI (GPT) provider"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        client = OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        return response.choices[0].message.content


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls"""
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Return simple mock responses based on prompt keywords
        last_message = messages[-1]["content"].lower()
        
        if "arpabet" in last_message or "phoneme" in last_message:
            return '{"arpabet": ["T", "EH1", "S", "T"]}'
        elif "json" in last_message:
            return '{"result": "mock response"}'
        elif "parse" in last_message or "query" in last_message:
            return '{"rhyme_type": "perfect", "syl_min": 2, "syl_max": 3}'
        else:
            return "Mock LLM response"


def get_provider(provider_name: str, api_key: str, model: str, **kwargs) -> LLMProvider:
    """Factory function to get appropriate provider"""
    
    providers = {
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,
        "mock": MockProvider,
        "test": MockProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
    
    return provider_class(api_key, model, **kwargs)
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client

def chat(messages: List[Dict[str, str]], model: str, max_tokens: int = 400) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""
