from datetime import datetime
from typing import Iterator, List
from uuid import UUID

import chromadb
from chromadb.api.types import Metadata, QueryResult

from src.vector_db.base import VectorDbBase
from src.vector_db.models import Chunk


class ChromaDbAdapter(VectorDbBase):
    def __init__(self, collection_name: str) -> None:
        # TODO: Support adding EmbeddingServiceBase and replacing ChromaDB default embedder.
        self._client = chromadb.Client()
        self._collection = self._client.create_collection(collection_name)

    def add_chunks(self, chunks: List[Chunk]) -> None:
        documents: List[str] = [chunk.content for chunk in chunks]
        ids: List[str] = [str(chunk.id) for chunk in chunks]

        metadatas: List[Metadata] = [
            {"modified_at": chunk.modified_at.isoformat(), "file_path": chunk.file_path}
            for chunk in chunks
        ]

        self._collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )

    def search(self, query: str, top_n: int) -> List[Chunk]:
        # TODO: Support filtering.
        results: QueryResult = self._collection.query(
            query_texts=[query],
            n_results=top_n,
        )

        ids = results["ids"][0]
        docs = results["documents"][0]  # type: ignore
        metas = results["metadatas"][0]  # type: ignore

        chunks_out: List[Chunk] = []

        for i in range(len(ids)):
            modified_at = metas[i].get("modified_at")
            if not isinstance(modified_at, str):
                raise ValueError(f"Expected str, got {type(modified_at)}.")
            modified_at = datetime.fromisoformat(modified_at)
            file_path = metas[i].get("file_path")
            if not isinstance(file_path, str):
                raise ValueError(f"Expected str, got {type(file_path)}.")

            chunks_out.append(
                Chunk(
                    id=UUID(ids[i]),
                    content=docs[i],
                    modified_at=modified_at,
                    file_path=file_path,
                )
            )

        return chunks_out

    def iter_chunks(self) -> Iterator[Chunk]:
        offset = 0
        limit = 100

        while True:
            results = self._collection.get(limit=limit, offset=offset)

            ids = results["ids"]

            if not ids:
                break

            docs = results["documents"] or []
            metas = results["metadatas"] or []

            for i in range(len(ids)):
                modified_at = metas[i].get("modified_at")
                if not isinstance(modified_at, str):
                    raise ValueError(f"Expected str, got {type(modified_at)}.")
                modified_at = datetime.fromisoformat(modified_at)
                file_path = metas[i].get("file_path")
                if not isinstance(file_path, str):
                    raise ValueError(f"Expected str, got {type(file_path)}.")
                yield Chunk(
                    id=UUID(ids[i]),
                    content=docs[i],
                    modified_at=modified_at,
                    file_path=file_path,
                )

            offset += limit
