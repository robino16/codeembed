from src.delta_computer.delta_computer import DeltaComputer
from src.doc_provider.base import DocProviderBase
from src.vector_db.base import VectorDbBase


class DocEmbedder:
    def ___init__(
        self,
        doc_provider: DocProviderBase,
        vector_db: VectorDbBase,
    ) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db

    def embed_codebase(self) -> None:

        files_to_delete, files_to_update = DeltaComputer(
            self._doc_provider, self._vector_db
        ).compute_deltas()
