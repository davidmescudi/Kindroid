"""
LLM module for handling language model interactions using LM Studio.
"""
from typing import Optional, Dict, Any, List
import httpx
from lmstudio import Client, UserMessage, AssistantResponse, SystemPrompt

from ..core.base import HardwareModule


class LLMModule(HardwareModule):
    """LLM module for handling language model interactions."""
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.api_url = self.config.get('api_url', 'http://localhost:1234/v1')
        self.model = self.config.get('model', 'local-model')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.system_prompt = self.config.get('system_prompt', '')
        self.conversation_history: List[Any] = []
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize the LLM module."""
        try:
            # Initialize LM Studio client
            self.client = Client(api_host=self.api_url)
            
            # Test connection by getting available models
            models = self.client.list_loaded_models()
            if len(models) > 0:
                # If model not specified or not available, use first available model
                if self.model == 'local-model' or self.model not in [m.id for m in models]:
                    self.model = models[0].id
                self.is_initialized = True
                return True
            return False
        except Exception as e:
            print(f"Failed to initialize LLM: {e}")
            return False
    
    def shutdown(self) -> bool:
        """Shutdown the LLM module."""
        self.is_initialized = False
        self.conversation_history.clear()
        if self.client:
            self.client.close()
        self.client = None
        return True
    
    def get_status(self) -> dict:
        """Get LLM module status."""
        return {
            "initialized": self.is_initialized,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "conversation_length": len(self.conversation_history)
        }
    
    def generate_response(self, user_input: str) -> Optional[str]:
        """
        Generate a response from the LLM.
        Args:
            user_input: The user's input text
        Returns:
            Generated response or None if failed
        """
        if not self.is_initialized:
            raise RuntimeError("LLM module not initialized")
        
        try:
            # Add user message to history
            user_message = UserMessage(content=user_input)
            self.conversation_history.append(user_message)
            
            # Prepare the messages list with system prompt
            messages = []
            if self.system_prompt:
                messages.append(SystemPrompt(content=self.system_prompt))
            messages.extend(self.conversation_history)
            
            # Generate completion using LM Studio client
            response = self.client.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if response and response.choices:
                assistant_message = response.choices[0].message
                
                # Add assistant response to history
                self.conversation_history.append(assistant_message)
                
                return assistant_message.content
            
            return None
                
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    def update_settings(self, **kwargs) -> bool:
        """
        Update LLM settings.
        Args:
            **kwargs: Settings to update (temperature, max_tokens, etc.)
        Returns:
            True if settings were updated successfully
        """
        try:
            if 'temperature' in kwargs:
                self.temperature = float(kwargs['temperature'])
            if 'max_tokens' in kwargs:
                self.max_tokens = int(kwargs['max_tokens'])
            if 'system_prompt' in kwargs:
                self.system_prompt = str(kwargs['system_prompt'])
            if 'model' in kwargs:
                self.model = str(kwargs['model'])
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def list_available_models(self) -> List[str]:
        """
        Get a list of available models.
        Returns:
            List of model IDs
        """
        if not self.is_initialized:
            raise RuntimeError("LLM module not initialized")
        
        try:
            models = self.client.list_loaded_models()
            return [model.id for model in models]
        except Exception as e:
            print(f"Error listing models: {e}")
            return [] 