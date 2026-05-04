from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple
from uuid import UUID

from codeembed.doc_provider.base import DocProviderBase
from codeembed.utils.time_utils import utc_now
from codeembed.vector_db.base import VectorDbBase


class DeltaComputer:
    """Figures out which files to add, delete or update."""

    def __init__(self, doc_provider: DocProviderBase, vector_db: VectorDbBase, debounce_seconds: int = 10) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db
        self._debounce_seconds = debounce_seconds

    def compute_deltas(self) -> Tuple[Set[UUID], Set[str]]:
        """
        Returns chunk IDs to delete and file paths to process.

        May not have best perfomance since we iterate each chunk stored in the vector database.
        """

        file_paths_to_update = set()

        file_path_to_chunk_ids: Dict[str, List[UUID]] = {}
        chunk_ids_to_delete: Set[UUID] = set()

        # Collect modified_at stored in our database.
        old_modified_at: Dict[str, datetime] = {}
        old_checksums: Dict[str, str] = {}
        for chunk in self._vector_db.iter_chunks():
            old_modified_at[chunk.file_path] = max(
                old_modified_at.get(chunk.file_path, chunk.modified_at), chunk.modified_at
            )
            old_checksums[chunk.file_path] = chunk.file_sha256_checksum

            file_path_to_chunk_ids[chunk.file_path] = file_path_to_chunk_ids.get(chunk.file_path, []) + [chunk.id]

        # Collect current modified_at in file system.
        current: Dict[str, datetime] = {}
        for doc in self._doc_provider.iter():
            current[doc.file_path] = doc.modified_at

        # Figure out which files have been added or modified.
        for file_path, modified_at in current.items():
            if modified_at > utc_now() - timedelta(seconds=self._debounce_seconds):
                # We skip files modified within the last N seconds
                continue

            if file_path not in old_modified_at or old_modified_at[file_path] < modified_at:
                if file_path in old_modified_at:
                    doc = self._doc_provider.get_content(file_path)
                    if doc.sha256_checksum == old_checksums[file_path]:
                        # We skip files with same checksum even if modified_at is updated.
                        # Some editors update modified_at even without any changes.
                        # TODO: We should probably update modified_at in vector database
                        #       to avoid re-reading this file on every run.
                        continue

                # file updated or added
                file_paths_to_update.add(file_path)

                # We delete all old chunks for any modified files.
                for chunk_id in file_path_to_chunk_ids.get(file_path, []):
                    chunk_ids_to_delete.add(chunk_id)

        # Figure out which files have been removed.
        for file_path in old_modified_at:
            if file_path not in current:
                for chunk_id in file_path_to_chunk_ids.get(file_path, []):
                    chunk_ids_to_delete.add(chunk_id)

        return chunk_ids_to_delete, file_paths_to_update
