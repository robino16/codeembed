from src.doc_provider.base import DocProviderBase
from src.vector_db.base import VectorDbBase


class DocEmbedder:
    def ___init__(self, doc_provider: DocProviderBase, vector_db: VectorDbBase) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db

    def embed_codebase(self) -> None:
        """Needs to compute deltas."""
