"""
Реализации различных языковых моделей для использования с LlamaIndex.
"""

import logging
import os

from github_rag_explorer.constants import DEFAULT_MODEL_NAMES
from github_rag_explorer.models.base import LLMBase
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIModel(LLMBase):
    """Класс для работы с моделями OpenAI."""

    def __init__(self, model_name: str = 'gpt-4o', **kwargs):
        """
        Инициализация модели OpenAI.

        Args:
            model_name: Название модели OpenAI
            **kwargs: Дополнительные параметры для OpenAI
        """
        super().__init__(model_name, **kwargs)
        self._llm = None

    def get_llm(self) -> OpenAI:
        """
        Получить инициализированный объект модели OpenAI.

        Returns:
            Объект OpenAI, готовый для использования с LlamaIndex
        """
        if self._llm is None:
            self._llm = OpenAI(model=self.model_name, **self.kwargs)
        return self._llm

    @property
    def provider_name(self) -> str:
        return 'openai'

    @classmethod
    def from_env(cls, model_name: str | None = None) -> 'OpenAIModel':
        """
        Создать экземпляр модели OpenAI, используя OPENAI_API_KEY из окружения.

        Args:
            model_name: Опциональное название модели, по умолчанию gpt-4o

        Returns:
            Инициализированный экземпляр OpenAIModel
        """
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.warning('OPENAI_API_KEY не найден в окружении')

        return cls(model_name or DEFAULT_MODEL_NAMES['openai'])


class AnthropicModel(LLMBase):
    """Класс для работы с моделями Anthropic Claude."""

    def __init__(self, model_name: str = 'claude-3-5-sonnet-latest', **kwargs):
        """
        Инициализация модели Anthropic.

        Args:
            model_name: Название модели Anthropic
            **kwargs: Дополнительные параметры для Anthropic
        """
        super().__init__(model_name, **kwargs)
        self._llm = None

    def get_llm(self) -> Anthropic:
        """
        Получить инициализированный объект модели Anthropic.

        Returns:
            Объект Anthropic, готовый для использования с LlamaIndex
        """
        if self._llm is None:
            self._llm = Anthropic(model=self.model_name, **self.kwargs)
        return self._llm

    @property
    def provider_name(self) -> str:
        return 'anthropic'

    @classmethod
    def from_env(cls, model_name: str | None = None) -> 'AnthropicModel':
        """
        Создать экземпляр модели Anthropic, используя ANTHROPIC_API_KEY из окружения.

        Args:
            model_name: Опциональное название модели

        Returns:
            Инициализированный экземпляр AnthropicModel
        """
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning('ANTHROPIC_API_KEY не найден в окружении')

        return cls(model_name or DEFAULT_MODEL_NAMES['anthropic'])


class OllamaModel(LLMBase):
    """Класс для работы с локальными моделями через Ollama."""

    def __init__(self, model_name: str = 'llama3', **kwargs):
        """
        Инициализация модели Ollama.

        Args:
            model_name: Название модели Ollama
            **kwargs: Дополнительные параметры для Ollama
        """
        super().__init__(model_name, **kwargs)
        self._llm = None

    def get_llm(self) -> Ollama:
        """
        Получить инициализированный объект модели Ollama.

        Returns:
            Объект Ollama, готовый для использования с LlamaIndex
        """
        if self._llm is None:
            self._llm = Ollama(model=self.model_name, **self.kwargs)
        return self._llm

    @property
    def provider_name(self) -> str:
        return 'ollama'

    @classmethod
    def from_env(cls, model_name: str | None = None) -> 'OllamaModel':
        """
        Создать экземпляр модели Ollama.

        Args:
            model_name: Опциональное название модели

        Returns:
            Инициализированный экземпляр OllamaModel
        """
        return cls(model_name or DEFAULT_MODEL_NAMES['ollama'])


def create_llm(provider: str, model_name: str | None = None) -> LLMBase:
    """
    Фабричный метод для создания экземпляра языковой модели по названию провайдера.

    Args:
        provider: Название провайдера модели (openai, anthropic, ollama)
        model_name: Опциональное название модели

    Returns:
        Экземпляр соответствующей модели

    Raises:
        ValueError: Если указан неизвестный провайдер
    """
    provider = provider.lower()

    if provider == 'openai':
        return OpenAIModel.from_env(model_name)
    elif provider == 'anthropic':
        return AnthropicModel.from_env(model_name)
    elif provider == 'ollama':
        return OllamaModel.from_env(model_name)
    else:
        raise ValueError(f'Неизвестный провайдер модели: {provider}')
