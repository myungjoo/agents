import os
import configparser
from abc import ABC, abstractmethod
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        """Generates text based on a prompt."""
        pass

class OpenAIProvider(LLMProvider):
    """Provider for OpenAI's GPT models (ChatGPT)."""
    def __init__(self):
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI library not found. Please run 'pip install openai'.")
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file.")
        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Or another preferred model
                messages=[
                    {"role": "system", "content": "You are a helpful assistant executing a task."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with OpenAI API: {e}"

class GeminiProvider(LLMProvider):
    """Provider for Google's Gemini models."""
    def __init__(self):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI library not found. Please run 'pip install google-generativeai'.")
            
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        try:
            # Note: Gemini's 'temperature' is part of generation_config
            generation_config = genai.types.GenerationConfig(temperature=temperature)
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text
        except Exception as e:
            return f"Error communicating with Gemini API: {e}"

class CursorProvider(LLMProvider):
    """Placeholder provider for Cursor."""
    def __init__(self):
        print("⚠️ WARNING: Cursor provider is a placeholder and not implemented.")
        # In a real scenario, you would add the Cursor API client and logic here.
        pass

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str:
        return f"--- CURSOR MOCK RESPONSE ---\nPrompt: {prompt}\nTemperature: {temperature}\n--- END MOCK ---"


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    provider_name = config.get('LLM', 'provider', fallback='openai').lower()

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "cursor":
        return CursorProvider()
    else:
        raise ValueError(f"Unsupported LLM provider '{provider_name}' in config.ini")


