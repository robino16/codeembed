from src.doc_search_service.doc_search_service import DocSearchService
from src.vector_db.chromadb_adapter import ChromaDbAdapter


def get_search_service() -> DocSearchService:
    vector_db = ChromaDbAdapter(collection_name="codebase_embeddings")
    search_service = DocSearchService(vector_db)
    return search_service
