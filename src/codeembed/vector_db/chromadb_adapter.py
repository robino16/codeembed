import json
from datetime import datetime
from typing import Dict, Iterator, List, Optional, Type, TypeVar
from uuid import UUID

import chromadb
from chromadb.api.types import Metadata, QueryResult

from codeembed.vector_db.base import VectorDbBase
from codeembed.vector_db.models import Chunk, SearchResult

T = TypeVar("T")


class ChromaDbAdapter(VectorDbBase):
    def __init__(self, collection_name: str) -> None:
        # TODO: Support adding EmbeddingServiceBase and replacing ChromaDB default embedder.
        self._client = chromadb.PersistentClient(path="./.codeembed")
        self._collection = self._client.get_or_create_collection(collection_name)

    def add_chunks(self, chunks: List[Chunk]) -> None:
        documents: List[str] = [chunk.content for chunk in chunks]
        ids: List[str] = [str(chunk.id) for chunk in chunks]

        metadatas: List[Metadata] = [
            {
                "modified_at": chunk.modified_at.isoformat(),
                "file_path": chunk.file_path,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "raw_code": chunk.raw_code,  # Assume ChromaDB can handle None values.
                "file_sha256_checksum": chunk.file_sha256_checksum,
                "graph_node_ids": json.dumps(chunk.graph_node_ids),
            }
            for chunk in chunks
        ]

        self._collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query: str, top_n: int) -> List[SearchResult]:
        # TODO: Support filtering.
        count = self._collection.count()
        if count == 0:
            return []
        results: QueryResult = self._collection.query(
            query_texts=[query],
            n_results=min(top_n, count),
        )

        ids = results["ids"][0]
        docs = results["documents"][0]  # type: ignore
        metas = results["metadatas"][0]  # type: ignore
        distances = results["distances"][0]  # type: ignore

        chunks_out: List[SearchResult] = []

        for i in range(len(ids)):
            # Can be simplified by adding a "get_safe_val" or similar.
            modified_at = self._get_safe_val(metas[i], "modified_at", str)
            modified_at = datetime.fromisoformat(modified_at)
            file_path = self._get_safe_val(metas[i], "file_path", str)
            line_start = self._get_safe_val(metas[i], "line_start", int)
            line_end = self._get_safe_val(metas[i], "line_end", int)
            raw_code = self._get_safe_val(metas[i], "raw_code", str, allow_none=True)
            file_sha256_checksum = self._get_safe_val(metas[i], "file_sha256_checksum", str)
            graph_node_ids = self._get_safe_list_val(metas[i], "graph_node_ids", str, allow_none=True)
            chunks_out.append(
                SearchResult(
                    chunk=Chunk(
                        id=UUID(ids[i]),
                        content=docs[i],
                        modified_at=modified_at,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        raw_code=raw_code,
                        file_sha256_checksum=file_sha256_checksum,
                        graph_node_ids=graph_node_ids,
                    ),
                    score=distances[i],
                )
            )

        return chunks_out

    def iter_chunks(self, where: Optional[Dict[str, str]] = None) -> Iterator[Chunk]:
        offset = 0
        limit = 100

        while True:
            results = self._collection.get(
                limit=limit,
                offset=offset,
                where=where,  # type: ignore
            )

            ids = results["ids"]

            if not ids:
                break

            docs = results["documents"] or []
            metas = results["metadatas"] or []

            for i in range(len(ids)):
                # Can be simplified by adding a "get_safe_val" or similar.
                modified_at = self._get_safe_val(metas[i], "modified_at", str)
                modified_at = datetime.fromisoformat(modified_at)
                file_path = self._get_safe_val(metas[i], "file_path", str)
                line_start = self._get_safe_val(metas[i], "line_start", int)
                line_end = self._get_safe_val(metas[i], "line_end", int)
                raw_code = self._get_safe_val(metas[i], "raw_code", str, allow_none=True)
                file_sha256_checksum = self._get_safe_val(metas[i], "file_sha256_checksum", str)
                graph_node_ids = self._get_safe_list_val(metas[i], "graph_node_ids", str, allow_none=True)
                yield Chunk(
                    id=UUID(ids[i]),
                    content=docs[i],
                    modified_at=modified_at,
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    raw_code=raw_code,
                    file_sha256_checksum=file_sha256_checksum,
                    graph_node_ids=graph_node_ids,
                )

            offset += limit

    def get_chunks(self, chunk_ids: List[UUID]) -> List[Chunk]:
        if not chunk_ids:
            return []
        str_chunk_ids = [str(chunk_id) for chunk_id in chunk_ids]
        results = self._collection.get(ids=str_chunk_ids)

        ids = results["ids"]
        docs = results["documents"] or []
        metas = results["metadatas"] or []

        chunks_out: List[Chunk] = []

        for i in range(len(ids)):
            # Can be simplified by adding a "get_safe_val" or similar.
            modified_at = self._get_safe_val(metas[i], "modified_at", str)
            modified_at = datetime.fromisoformat(modified_at)
            file_path = self._get_safe_val(metas[i], "file_path", str)
            line_start = self._get_safe_val(metas[i], "line_start", int)
            line_end = self._get_safe_val(metas[i], "line_end", int)
            raw_code = self._get_safe_val(metas[i], "raw_code", str, allow_none=True)
            file_sha256_checksum = self._get_safe_val(metas[i], "file_sha256_checksum", str)
            graph_node_ids = self._get_safe_list_val(metas[i], "graph_node_ids", str, allow_none=True)
            chunks_out.append(
                Chunk(
                    id=UUID(ids[i]),
                    content=docs[i],
                    modified_at=modified_at,
                    file_path=file_path,
                    line_start=line_start,
                    line_end=line_end,
                    raw_code=raw_code,
                    file_sha256_checksum=file_sha256_checksum,
                    graph_node_ids=graph_node_ids,
                )
            )

        return chunks_out

    def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        # Maybe batch if list is very long? I hope ChromaDB does so internally.
        self._collection.delete(ids=[str(chunk_id) for chunk_id in chunk_ids])

    def _get_safe_list_val(
        self, meta: Metadata, key: str, expected_elem_type: Type[T], allow_none: bool = False
    ) -> List[T]:
        val_str = self._get_safe_val(meta, key, str, allow_none=allow_none)
        if val_str is None and allow_none:
            return []
        elif val_str is None:
            raise ValueError(f"Expected a JSON string for key '{key}', got None.")
        val_json = json.loads(val_str)
        if not isinstance(val_json, list):
            raise ValueError(f"Expected a list for key '{key}', got {type(val_json)}.")
        for elem in val_json:
            if not isinstance(elem, expected_elem_type):
                raise ValueError(
                    f"Expected elements of type {expected_elem_type} in list for "
                    f"key '{key}', got element of type {type(elem)}."
                )
        return val_json

    def _get_safe_val(self, meta: Metadata, key: str, expected_type: Type[T], allow_none: bool = False) -> T:
        val = meta.get(key)
        if val is None and allow_none:
            return None  # type: ignore
        if not isinstance(val, expected_type):
            raise ValueError(f"Expected {expected_type}, got {type(val)} for ChromaDB metadata key '{key}'.")
        return val
