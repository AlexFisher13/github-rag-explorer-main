"""
Модули для выполнения запросов к индексам.
"""

import logging
from typing import Any

from github_rag_explorer.models.llm import create_llm
from llama_index.core import Settings, VectorStoreIndex

logger = logging.getLogger(__name__)


class QueryEngine:
    """Класс для выполнения запросов к индексу."""

    def __init__(
        self,
        index: VectorStoreIndex,
        model_provider: str | None = None,
        model_name: str | None = None,
    ):
        """
        Инициализация движка запросов.

        Args:
            index: Индекс для запросов
            model_provider: Опционально, провайдер модели для запросов
            model_name: Опционально, название модели для запросов
        """
        self.index = index
        self.model_provider = model_provider
        self.model_name = model_name

        # Настройка LLM, если указаны провайдер и модель
        if model_provider and model_name:
            self._setup_llm()

    def _setup_llm(self):
        """Настройка языковой модели для запросов."""
        if self.model_provider and self.model_name:
            llm = create_llm(self.model_provider, self.model_name)
            Settings.llm = llm.get_llm()

    def query(self, query_text: str, top_k: int = 5) -> str:
        """
        Выполнить запрос к индексу.

        Args:
            query_text: Текст запроса
            top_k: Количество результатов для возврата

        Returns:
            Ответ на запрос
        """
        logger.info(f'Выполнение запроса: {query_text}')

        # Создание движка запросов
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
        )

        # Выполнение запроса
        response = query_engine.query(query_text)

        return str(response)


class SourceDetail:
    """Класс для получения деталей об исходном источнике данных."""

    @staticmethod
    def get_source_type(source_info: dict[str, Any]) -> str:
        """
        Получить тип источника данных.

        Args:
            source_info: Информация о источнике

        Returns:
            Тип источника (github, local)
        """
        return source_info.get('type', 'unknown')

    @staticmethod
    def format_source_info(source_info: dict[str, Any]) -> str:
        """
        Форматировать информацию об источнике в виде строки.

        Args:
            source_info: Информация о источнике

        Returns:
            Отформатированная строка с информацией
        """
        source_type = SourceDetail.get_source_type(source_info)

        if source_type == 'github':
            return (
                f'Индекс для репозитория: **{source_info.get("owner", "N/A")}/{source_info.get("repo", "N/A")}** '
                f'(ветка: {source_info.get("branch", "N/A")})\n\n'
                f'Всего документов: {source_info.get("total_documents", "N/A")}\n\n'
                f'Модель: {source_info.get("model_provider", "N/A")} / {source_info.get("model_name", "N/A")}'
            )
        elif source_type == 'local':
            return (
                f'Индекс для локальной директории: **{source_info.get("directory", "N/A")}**\n\n'
                f'Всего документов: {source_info.get("total_documents", "N/A")}\n\n'
                f'Модель: {source_info.get("model_provider", "N/A")} / {source_info.get("model_name", "N/A")}'
            )
        else:
            return f'Неизвестный тип источника: {source_type}'
