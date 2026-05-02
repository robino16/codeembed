from datetime import datetime
from typing import Dict, Set, Tuple

from src.doc_provider.base import DocProviderBase
from src.vector_db.base import VectorDbBase


class DeltaComputer:
    """Figures out which files to add, delete or update."""

    def __init__(self, doc_provider: DocProviderBase, vector_db: VectorDbBase) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db

    def compute_deltas(self) -> Tuple[Set[str], Set[str]]:
        """
        Computing deltas is really easy.

        We iter each chunk in the vector database directly, which is not the best in terms of performance.
        """

        file_paths_to_delete = set()
        file_paths_to_update = set()

        # Collect modified_at stored in our database.
        old: Dict[str, datetime] = {}
        for chunk in self._vector_db.iter_chunks():
            old[chunk.file_path] = max(
                old.get(chunk.file_path, chunk.modified_at), chunk.modified_at
            )

        # Collect current modified_at in file system.
        current: Dict[str, datetime] = {}
        for doc in self._doc_provider.iter():
            current[doc.file_path] = doc.modified_at

        # Figure out which files have been added or modified.
        for file_path, modified_at in current.items():
            if file_path not in old or old[file_path] < modified_at:
                file_paths_to_update.add(file_path)

        # Figure out which files have been removed.
        for file_path in old:
            if file_path not in current:
                file_paths_to_delete.add(file_path)

        return file_paths_to_delete, file_paths_to_update
