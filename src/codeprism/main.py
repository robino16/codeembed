import logging

from codeprism.bootstrap.services import get_embedder_service, get_search_service
from codeprism.setup_logger import setup_logger

logger = logging.getLogger(__name__)


def main():
    setup_logger()

    logger.info("Starting codebase embedding process...")

    embedder = get_embedder_service()
    search_service = get_search_service()

    embedder.embed_codebase()

    search_query = "How does this code use LLMs?"
    search_result = search_service.search(search_query, top_n=5)

    print("Search result:")
    print(search_result)

    logger.info("Done!")


if __name__ == "__main__":
    main()
