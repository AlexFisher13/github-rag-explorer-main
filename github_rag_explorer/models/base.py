"""
Базовые классы и интерфейсы для языковых моделей.
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMBase(ABC):
    """
    Базовый абстрактный класс для всех языковых моделей.
    Определяет общий интерфейс для работы с разными LLM.
    """

    @abstractmethod
    def __init__(self, model_name: str, **kwargs):
        """
        Инициализация языковой модели.

        Args:
            model_name: Название модели для использования
            **kwargs: Дополнительные параметры для инициализации модели
        """
        self.model_name = model_name
        self.kwargs = kwargs

    @abstractmethod
    def get_llm(self) -> Any:
        """
        Получить инициализированный объект языковой модели.

        Returns:
            Объект модели, готовый для использования с LlamaIndex
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Название провайдера модели.

        Returns:
            Строка с названием провайдера
        """
        pass

    @classmethod
    @abstractmethod
    def from_env(cls, model_name: str | None = None) -> 'LLMBase':
        """
        Создать экземпляр модели, используя переменные окружения для API ключей.

        Args:
            model_name: Опциональное название модели

        Returns:
            Инициализированный экземпляр модели
        """
        pass
