from datetime import datetime
from typing import Dict, List, Set, Tuple
from uuid import UUID

from src.doc_provider.base import DocProviderBase
from src.vector_db.base import VectorDbBase


class DeltaComputer:
    """Figures out which files to add, delete or update."""

    def __init__(self, doc_provider: DocProviderBase, vector_db: VectorDbBase) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db

    def compute_deltas(self) -> Tuple[Set[UUID], Set[str]]:
        """
        Returns chunk IDs to delete and file paths to process.

        May not have best perfomance since we iterate each chunk stored in the vector database.
        """

        file_paths_to_update = set()

        file_path_to_chunk_ids: Dict[str, List[UUID]] = {}
        chunk_ids_to_delete: Set[UUID] = set()

        # Collect modified_at stored in our database.
        old: Dict[str, datetime] = {}
        for chunk in self._vector_db.iter_chunks():
            old[chunk.file_path] = max(
                old.get(chunk.file_path, chunk.modified_at), chunk.modified_at
            )

            file_path_to_chunk_ids[chunk.file_path] = file_path_to_chunk_ids.get(
                chunk.file_path, []
            ) + [chunk.id]

        # Collect current modified_at in file system.
        current: Dict[str, datetime] = {}
        for doc in self._doc_provider.iter():
            current[doc.file_path] = doc.modified_at

        # Figure out which files have been added or modified.
        for file_path, modified_at in current.items():
            if file_path not in old or old[file_path] < modified_at:
                file_paths_to_update.add(file_path)

            # We delete all old chunks for any modified files.
            for chunk_id in file_path_to_chunk_ids.get(file_path, []):
                chunk_ids_to_delete.add(chunk_id)

        # Figure out which files have been removed.
        for file_path in old:
            if file_path not in current:
                for chunk_id in file_path_to_chunk_ids.get(file_path, []):
                    chunk_ids_to_delete.add(chunk_id)

        return chunk_ids_to_delete, file_paths_to_update
