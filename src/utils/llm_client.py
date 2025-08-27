"""
LLM client for interacting with various language model APIs.
Supports OpenAI and Anthropic models with unified interface.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Unified client for interacting with different LLM providers."""
    
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = LLMProvider(provider.lower())
        self.model = model or self._get_default_model()
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        self._initialize_client()
    
    def _get_default_model(self) -> str:
        """Get default model for the provider."""
        if self.provider == LLMProvider.OPENAI:
            return os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        elif self.provider == LLMProvider.ANTHROPIC:
            return os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == LLMProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI library not installed. Run: pip install openai")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            self.client = OpenAI(api_key=api_key)
            
        elif self.provider == LLMProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic library not installed. Run: pip install anthropic")
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required")
            
            self.client = Anthropic(api_key=api_key)
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def generate_response(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.3,
        response_format: Optional[str] = None
    ) -> str:
        """Generate response from LLM."""
        try:
            if self.provider == LLMProvider.OPENAI:
                return await self._call_openai(
                    prompt, system_message, max_tokens, temperature, response_format
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._call_anthropic(
                    prompt, system_message, max_tokens, temperature
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")
    
    async def _call_openai(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float,
        response_format: Optional[str]
    ) -> str:
        """Call OpenAI API."""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add response format if specified and supported
        if response_format == "json" and "gpt-4" in self.model.lower():
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    async def _call_anthropic(
        self,
        prompt: str,
        system_message: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Call Anthropic API."""
        system = system_message or "You are a helpful AI assistant."
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.strip()
            return json.loads(clean_response)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"LLM returned invalid JSON format: {e}")
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider and model."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "available": True
        }


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
        """Create LLM client based on environment or parameters."""
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "openai")
        
        return LLMClient(provider=provider, model=model)
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available providers."""
        providers = []
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            providers.append("anthropic")
        
        return providers