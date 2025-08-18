"""
Модули для загрузки и обработки данных из различных источников.
"""

from github_rag_explorer.data.loader import (
    BaseLoader,
    GitHubLoader,
    LocalDirectoryLoader,
)
from github_rag_explorer.data.processor import (
    DocumentProcessor,
    detect_language,
)

__all__ = [
    'BaseLoader',
    'GitHubLoader',
    'LocalDirectoryLoader',
    'DocumentProcessor',
    'detect_language',
]
