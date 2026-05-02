from datetime import datetime
from typing import Dict, List, Union
from uuid import UUID

import chromadb
from chromadb.api.types import Metadata, QueryResult

from src.types import CommonType
from src.vector_db.base import VectorDbBase
from src.vector_db.models import Chunk

_ChromaDbMetadataType = Union[str, int, float, bool]


class _ChromaDBMetadataMapper:
    @staticmethod
    def to_chromadb(
        metadata_in: Dict[str, CommonType],
    ) -> Dict[str, _ChromaDbMetadataType]:
        metadata_out: Dict[str, _ChromaDbMetadataType] = {}

        for key, val in metadata_in.items():
            if isinstance(val, (str, int, float, bool)):
                metadata_out[key] = val
            elif isinstance(val, datetime):
                metadata_out[key] = val.isoformat()
            elif val is None:
                continue
            else:
                raise ValueError(f"Unsupported metadata type {type(val)}.")

        return metadata_out

    @staticmethod
    def from_chromadb(
        metadata_in: Dict[str, _ChromaDbMetadataType],
    ) -> Dict[str, CommonType]:
        metadata_out: Dict[str, CommonType] = {}

        for key, val in metadata_in.items():
            if isinstance(val, str):
                try:
                    parsed: datetime = datetime.fromisoformat(val)
                    metadata_out[key] = parsed
                    continue
                except ValueError:
                    pass
            metadata_out[key] = val
        return metadata_out


class ChromaDbAdapter(VectorDbBase):
    def __init__(self, collection_name: str) -> None:
        # TODO: Support adding EmbeddingServiceBase and replacing ChromaDB default embedder.
        self._client = chromadb.Client()
        self._collection = self._client.create_collection(collection_name)

    def add_chunks(self, chunks: List[Chunk]) -> None:
        documents: List[str] = [chunk.content for chunk in chunks]
        ids: List[str] = [str(chunk.id) for chunk in chunks]

        metadatas: List[Metadata] = [
            _ChromaDBMetadataMapper.to_chromadb(chunk.metadata) for chunk in chunks
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

        ids: List[str] = results["ids"][0]  # type: ignore
        docs: List[str] = results["documents"][0]  # type: ignore

        if results["metadatas"] is None:
            metas: List[Dict[str, _ChromaDbMetadataType]] = [{} for _ in ids]
        else:
            metas = results["metadatas"][0]  # type: ignore

        chunks_out: List[Chunk] = []

        for i in range(len(ids)):
            chunks_out.append(
                Chunk(
                    id=UUID(ids[i]),
                    content=docs[i],
                    metadata=_ChromaDBMetadataMapper.from_chromadb(metas[i]),
                )
            )

        return chunks_out
