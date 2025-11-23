"""
LiteLLM-based LLM Provider for Inferno.

Provides a unified interface for all LLM providers using LiteLLM.
Supports: OpenAI, Anthropic, DeepSeek, Ollama, and 100+ other providers.

Configuration via .env:
    LLM_PROVIDER: Provider name (openai, anthropic, deepseek, ollama, etc.)
    LLM_MODEL: Model name (e.g., gpt-4, claude-3-5-sonnet-20241022, deepseek-reasoner)
    LLM_API_KEY: API key for the provider
    LLM_BASE_URL: Optional custom base URL (for Ollama, custom endpoints)
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import litellm

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True
litellm.set_verbose = False


@dataclass
class LLMResponse:
    """Unified LLM response format."""
    output: List[Any]  # List of message/function_call objects
    usage: Optional[Dict] = None
    raw_response: Any = None
    reasoning: Optional[str] = None  # Captured reasoning/thought process


class LiteLLMProvider:
    """
    Unified LLM provider using LiteLLM.
    
    Automatically handles format conversions for all providers including:
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude 3.5 Sonnet, etc.)
    - DeepSeek (DeepSeek-Reasoner, DeepSeek-Chat)
    - Ollama (Llama3, Mistral, etc.)
    - And 100+ other providers
    """
    
    def __init__(
        self,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize LiteLLM provider.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic', 'deepseek', 'ollama')
            model: Model name (e.g., 'gpt-4', 'claude-3-5-sonnet-20241022')
            api_key: API key for the provider
            base_url: Optional custom base URL
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        
        # Build full model name for LiteLLM
        # Format: "provider/model" or just "model" for OpenAI
        if self.provider == "openai":
            self.litellm_model = model
        elif self.provider == "ollama":
            self.litellm_model = f"ollama/{model}"
        elif self.provider == "anthropic":
            self.litellm_model = f"anthropic/{model}"
        elif self.provider == "deepseek":
            self.litellm_model = f"deepseek/{model}"
        else:
            # For other providers, use provider/model format
            self.litellm_model = f"{self.provider}/{model}"
        
        # Set API key in environment for LiteLLM
        if api_key:
            if self.provider == "openai":
                os.environ["OPENAI_API_KEY"] = api_key
            elif self.provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif self.provider == "deepseek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            # Ollama doesn't need API key
        
        # Set base URL if provided
        if base_url:
            if self.provider == "ollama":
                os.environ["OLLAMA_API_BASE"] = base_url
            elif self.provider == "deepseek":
                litellm.api_base = base_url
        
        logger.info(f"Initialized LiteLLM provider: {self.litellm_model}")
    
    async def create_response(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        reasoning_effort: str = "high",
        metadata: Optional[Dict] = None
    ) -> LLMResponse:
        """
        Create response using LiteLLM.
        
        LiteLLM automatically handles all format conversions between providers.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            reasoning_effort: Reasoning effort level (for models that support it)
            metadata: Optional metadata dictionary
            
        Returns:
            LLMResponse with unified format
        """
        # LiteLLM handles all format conversions automatically!
        # But we need to ensure tools are in the correct structure first
        
        # Normalize tools to OpenAI format if they are in the flat format from main.py
        normalized_tools = []
        if tools:
            for tool in tools:
                # Check if it's the flat format from main.py: {"type": "function", "name": ...}
                if tool.get("type") == "function" and "function" not in tool and "name" in tool:
                    normalized_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.get("name"),
                            "description": tool.get("description"),
                            "parameters": tool.get("parameters"),
                            "strict": False  # Disable strict mode to avoid validation errors with optional params
                        }
                    })
                else:
                    # Ensure strict is False for existing OpenAI format tools too if possible
                    if "function" in tool:
                        tool["function"]["strict"] = False
                    normalized_tools.append(tool)
        
        # Normalize messages to OpenAI format
        # main.py uses Anthropic format: {"role": "developer", "content": [{"type": "input_text", "text": ...}]}
        normalized_messages = []
        
        # First pass: Convert formats and collect messages
        temp_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                temp_messages.append(msg)
                continue
            
            msg_copy = msg.copy()
            
            # Convert role: developer -> system
            if msg_copy.get('role') == 'developer':
                msg_copy['role'] = 'system'
            
            # Convert content from Anthropic format (blocks) to OpenAI format (string)
            content = msg_copy.get('content')
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') in ['input_text', 'text']:
                            text_parts.append(block.get('text', ''))
                        elif 'text' in block:
                            text_parts.append(block['text'])
                
                if text_parts:
                    msg_copy['content'] = '\n'.join(text_parts)
            
            # Handle function call outputs (tool results)
            if msg_copy.get('type') == 'function_call_output':
                temp_messages.append({
                    'role': 'tool',
                    'tool_call_id': msg_copy.get('call_id', ''),
                    'content': str(msg_copy.get('output', ''))
                })
                continue
            
            temp_messages.append(msg_copy)
            
        # Second pass: Merge function_call objects into preceding assistant message
        final_messages = []
        current_assistant_msg = None
        
        for msg in temp_messages:
            # If it's a function_call object (from main.py's history)
            if isinstance(msg, dict) and msg.get('type') == 'function_call':
                if current_assistant_msg:
                    # Initialize tool_calls if not present
                    if 'tool_calls' not in current_assistant_msg:
                        current_assistant_msg['tool_calls'] = []
                    
                    # Add this function call to the assistant message
                    current_assistant_msg['tool_calls'].append({
                        'id': msg.get('call_id', ''),
                        'type': 'function',
                        'function': {
                            'name': msg.get('name', ''),
                            'arguments': msg.get('arguments', '{}')
                        }
                    })
                else:
                    # Orphaned function call (no preceding text message)
                    # Create a new assistant message to hold it
                    current_assistant_msg = {
                        "role": "assistant",
                        "content": "",  # Use empty string for DeepSeek compatibility
                        "tool_calls": []
                    }
                    final_messages.append(current_assistant_msg)
                
                # Add this function call to the assistant message
                if 'tool_calls' not in current_assistant_msg:
                    current_assistant_msg['tool_calls'] = []
                
                # Check for duplicates to prevent DeepSeek errors
                call_id = msg.get('call_id', '')
                existing_ids = {tc['id'] for tc in current_assistant_msg['tool_calls']}
                
                if call_id and call_id not in existing_ids:
                    current_assistant_msg['tool_calls'].append({
                        'id': call_id,
                        'type': 'function',
                        'function': {
                            'name': msg.get('name', ''),
                            'arguments': msg.get('arguments', '{}')
                        }
                    })
                continue
            
            # If it's an assistant message, track it as current
            if isinstance(msg, dict) and (msg.get('role') == 'assistant' or msg.get('type') == 'message'):
                # Ensure it has role=assistant if it was type=message
                if msg.get('type') == 'message':
                    msg['role'] = 'assistant'
                    # Extract content if needed (already done in first pass usually)
                    if isinstance(msg.get('content'), list):
                         # If content is still list of objects (from ResponseObject)
                         text = ""
                         for item in msg['content']:
                             if hasattr(item, 'text'):
                                 text += item.text
                             elif isinstance(item, dict) and 'text' in item:
                                 text += item['text']
                         msg['content'] = text

                current_assistant_msg = msg
                final_messages.append(msg)
            else:
                # Any other message (system, user, tool) resets current assistant
                current_assistant_msg = None
                final_messages.append(msg)

        params = {
            "model": self.litellm_model,
            "messages": final_messages,
        }
        
        if normalized_tools:
            params["tools"] = normalized_tools
        
        # Add metadata as custom parameters if needed
        if metadata:
            params["metadata"] = metadata
        
        try:
            # Call LiteLLM's completion endpoint
            response = await litellm.acompletion(**params)
            
            # Convert to unified format
            return self._convert_response(response)
            
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
            raise
    
    def _convert_response(self, litellm_response: Any) -> LLMResponse:
        """
        Convert LiteLLM response to Inferno's unified format.
        
        LiteLLM returns OpenAI-compatible format, which we convert to
        the format expected by main.py (with .type attributes).
        """
        output = []
        reasoning = None
        
        # Extract message from response
        if hasattr(litellm_response, 'choices') and litellm_response.choices:
            choice = litellm_response.choices[0]
            message = choice.message
            
            # Extract reasoning content if available (DeepSeek, etc.)
            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                reasoning = message.reasoning_content
            elif hasattr(message, 'provider_specific_fields') and message.provider_specific_fields:
                # Check for reasoning in provider specific fields
                reasoning = message.provider_specific_fields.get('reasoning_content')
            
            # Create JSON-serializable object with attribute access
            class ResponseObject(dict):
                """Dict that also supports attribute access."""
                def __init__(self, **kwargs):
                    super().__init__(kwargs)
                    self.__dict__ = self
                
                def __getattr__(self, key):
                    try:
                        return self[key]
                    except KeyError:
                        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
            
            # Add message content if present
            if hasattr(message, 'content') and message.content:
                output.append(ResponseObject(
                    type="message",
                    content=[ResponseObject(type="text", text=message.content)]
                ))
            
            # Add tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    output.append(ResponseObject(
                        type="function_call",
                        name=tool_call.function.name,
                        call_id=tool_call.id,
                        arguments=tool_call.function.arguments
                    ))
        
        # Extract usage stats
        usage = None
        if hasattr(litellm_response, 'usage'):
            usage = {
                "input_tokens": litellm_response.usage.prompt_tokens,
                "output_tokens": litellm_response.usage.completion_tokens,
            }
        
        return LLMResponse(
            output=output,
            usage=usage,
            raw_response=litellm_response,
            reasoning=reasoning
        )


def create_llm_provider(
    provider: str,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> LiteLLMProvider:
    """
    Factory function to create LLM provider.
    
    Args:
        provider: Provider name (openai, anthropic, deepseek, ollama, etc.)
        model: Model name
        api_key: API key
        base_url: Optional base URL
        
    Returns:
        LiteLLMProvider instance
        
    Raises:
        ValueError: If API key is required but missing
    """
    # Check if API key is required
    if provider.lower() not in ["ollama"] and not api_key:
        raise ValueError(f"API key required for {provider} provider")
    
    return LiteLLMProvider(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url
    )

# Alias for backward compatibility
LLMProvider = LiteLLMProvider
