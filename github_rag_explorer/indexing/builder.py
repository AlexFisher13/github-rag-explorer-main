"""
Модули для построения и управления индексами.
"""

import json
import logging
import os
from pathlib import Path

from github_rag_explorer.models.llm import create_llm
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)

logger = logging.getLogger(__name__)


class IndexBuilder:
    """Класс для построения и загрузки индексов."""

    def __init__(
        self,
        model_provider: str,
        model_name: str | None = None,
        index_path: str | None = None,
    ):
        """
        Инициализация построителя индексов.

        Args:
            model_provider: Название провайдера языковой модели
            model_name: Имя модели
            index_path: Путь для сохранения индекса
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.index_path = index_path
        self._setup_llm()

    def _setup_llm(self):
        """Настройка языковой модели для индексации."""
        llm = create_llm(self.model_provider, self.model_name)
        Settings.llm = llm.get_llm()

    def build_index(self, documents: list[Document]) -> VectorStoreIndex:
        """
        Построить индекс из списка документов.

        Args:
            documents: Список документов для индексации

        Returns:
            Созданный индекс
        """
        logger.info('Построение индекса...')

        # Создание индекса
        index = VectorStoreIndex.from_documents(documents)

        # Сохранение индекса, если указан путь
        if self.index_path:
            self.save_index(index)

        return index

    def save_index(self, index: VectorStoreIndex) -> None:
        """
        Сохранить индекс и информацию о модели.

        Args:
            index: Индекс для сохранения
        """
        if not self.index_path:
            logger.warning('Путь для сохранения индекса не указан')
            return

        logger.info(f'Сохранение индекса в {self.index_path}')

        # Создаем директорию, если она не существует
        Path(self.index_path).mkdir(parents=True, exist_ok=True)

        # Сохранение индекса
        index.storage_context.persist(persist_dir=self.index_path)

        # Сохранение информации о модели
        model_info = {
            'provider': self.model_provider,
            'model_name': self.model_name,
        }

        with open(Path(self.index_path) / 'model_info.json', 'w') as f:
            json.dump(model_info, f, indent=4)


class IndexLoader:
    """Класс для загрузки существующих индексов."""

    def __init__(
        self,
        index_path: str,
        model_provider: str | None = None,
        model_name: str | None = None,
    ):
        """
        Инициализация загрузчика индексов.

        Args:
            index_path: Путь к сохраненному индексу
            model_provider: Опционально, провайдер модели для запросов
            model_name: Опционально, название модели для запросов
        """
        self.index_path = index_path
        self.model_provider = model_provider
        self.model_name = model_name

    def load(self) -> VectorStoreIndex | None:
        """
        Загрузить индекс из указанного пути.

        Returns:
            Загруженный индекс или None в случае ошибки
        """
        try:
            logger.info(f'Загрузка индекса из {self.index_path}')

            # Проверяем существование директории
            if not os.path.exists(self.index_path):
                logger.error(
                    f'Директория индекса не существует: {self.index_path}'
                )
                return None

            # Загрузка информации о модели, если не указаны явно
            model_provider = self.model_provider
            model_name = self.model_name

            model_info_path = Path(self.index_path) / 'model_info.json'
            if model_info_path.exists() and not (model_provider and model_name):
                with open(model_info_path) as f:
                    model_info = json.load(f)
                    model_provider = model_provider or model_info.get(
                        'provider', 'openai'
                    )
                    model_name = model_name or model_info.get('model_name')

            # Настройка языковой модели
            llm = create_llm(model_provider or 'openai', model_name)
            Settings.llm = llm.get_llm()

            # Загрузка индекса
            storage_context = StorageContext.from_defaults(
                persist_dir=self.index_path
            )
            return load_index_from_storage(storage_context)

        except Exception as e:
            logger.error(f'Ошибка при загрузке индекса: {e}')
            return None


def save_source_info(
    index_path: str,
    source_type: str,
    total_documents: int,
    model_provider: str,
    model_name: str | None,
    **kwargs,
) -> None:
    """
    Сохранить информацию об источнике данных.

    Args:
        index_path: Путь к индексу
        source_type: Тип источника (github, local)
        total_documents: Общее количество документов
        model_provider: Провайдер модели
        model_name: Имя модели
        **kwargs: Дополнительные метаданные для сохранения
    """
    import time

    # Создание базовой информации
    source_info = {
        'type': source_type,
        'total_documents': total_documents,
        'index_path': index_path,
        'model_provider': model_provider,
        'model_name': model_name,
        'timestamp': str(time.time()),
    }

    # Добавление дополнительных метаданных
    source_info.update(kwargs)

    # Сохранение информации в JSON файл
    with open(Path(index_path) / 'source_info.json', 'w') as f:
        json.dump(source_info, f, indent=4)
