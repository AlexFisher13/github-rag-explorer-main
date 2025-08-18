"""
Модули для обработки и предобработки документов перед индексацией.
"""

import logging

from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

from github_rag_explorer.constants import (
    DEFAULT_CHUNK_LINES,
    DEFAULT_CHUNK_LINES_OVERLAP,
    DEFAULT_MAX_CHARS,
)
from llama_index.core import Document
from llama_index.core.node_parser import CodeSplitter
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)


def detect_language(file_path: str) -> str | None:
    """
    Определение языка программирования по имени файла с помощью Pygments.

    Args:
        file_path: Путь к файлу

    Returns:
        Название языка программирования или None, если язык не определен
    """
    try:
        lexer = get_lexer_for_filename(file_path)
        return lexer.name.lower()
    except ClassNotFound:
        return None


class DocumentProcessor:
    """Класс для обработки документов перед индексацией."""

    def __init__(
        self,
        chunk_lines: int = DEFAULT_CHUNK_LINES,
        chunk_lines_overlap: int = DEFAULT_CHUNK_LINES_OVERLAP,
        max_chars: int = DEFAULT_MAX_CHARS,
    ):
        """
        Инициализация процессора документов.

        Args:
            chunk_lines: Количество строк в одном чанке
            chunk_lines_overlap: Перекрытие строк между чанками
            max_chars: Максимальное количество символов в чанке
        """
        self.chunk_lines = chunk_lines
        self.chunk_lines_overlap = chunk_lines_overlap
        self.max_chars = max_chars

    def process(self, documents: list[Document]) -> list[Document]:
        """
        Обработать список документов.

        Args:
            documents: Список документов для обработки

        Returns:
            Список обработанных документов
        """
        processed_docs = []

        for doc in documents:
            processed_chunks = self._process_document(doc)
            processed_docs.extend(processed_chunks)

        logger.info(f'После предобработки: {len(processed_docs)} документов')
        return processed_docs

    def _process_document(self, document: Document) -> list[Document]:
        """
        Обработать один документ.

        Args:
            document: Документ для обработки

        Returns:
            Список обработанных документов (чанков)
        """
        # Извлечение пути к файлу из метаданных
        file_path = document.metadata.get('file_path', '')
        if not file_path:
            # Если нет пути, просто возвращаем документ как есть
            return [document]

        # Определение языка программирования
        language = detect_language(file_path)

        if language:
            # Создаем разделитель кода с учетом языка
            try:
                splitter = CodeSplitter(
                    language=language,
                    chunk_lines=self.chunk_lines,
                    chunk_lines_overlap=self.chunk_lines_overlap,
                    max_chars=self.max_chars,
                )

                # Получение нод из документа
                nodes = splitter.get_nodes_from_documents([document])

                # Преобразование нод обратно в документы
                processed_chunks = []
                for i, node in enumerate(nodes):
                    # Копирование метаданных и добавление информации о чанке
                    chunk_metadata = dict(document.metadata)
                    chunk_metadata['chunk_index'] = i
                    chunk_metadata['language'] = language
                    chunk_metadata['total_chunks'] = len(nodes)

                    # Объединяем метаданные ноды и документа
                    if isinstance(node, TextNode):
                        # Если имеет метаданные, объединяем их
                        node_metadata = node.metadata or {}
                        for key, value in chunk_metadata.items():
                            if key not in node_metadata:
                                node_metadata[key] = value

                        processed_chunks.append(
                            Document(text=node.text, metadata=node_metadata)
                        )
                    else:
                        # Обычное добавление документа
                        processed_chunks.append(
                            Document(
                                text=node.get_content(), metadata=chunk_metadata
                            )
                        )

                return processed_chunks

            except Exception as e:
                logger.warning(
                    f'Ошибка при разделении файла {file_path}: {e}. Используем документ целиком.'
                )
                # Если произошла ошибка при разделении, используем документ как есть
                return [document]
        else:
            # Если язык не определен, просто возвращаем документ как есть
            return [document]
