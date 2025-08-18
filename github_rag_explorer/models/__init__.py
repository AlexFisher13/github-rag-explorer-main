"""
Модели и классы для работы с языковыми моделями разных провайдеров.
"""

from github_rag_explorer.models.base import LLMBase
from github_rag_explorer.models.llm import (
    AnthropicModel,
    OllamaModel,
    OpenAIModel,
    create_llm,
)

__all__ = [
    'LLMBase',
    'OpenAIModel',
    'AnthropicModel',
    'OllamaModel',
    'create_llm',
]
