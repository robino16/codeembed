import logging
from uuid import uuid4

from codeprism.delta_computer.delta_computer import DeltaComputer
from codeprism.doc_provider.base import DocProviderBase
from codeprism.doc_splitters.factory import DocSplitterFactory
from codeprism.doc_splitters.models import FileSegment
from codeprism.llm.base import LLMServiceBase
from codeprism.vector_db.base import VectorDbBase
from codeprism.vector_db.models import Chunk

logger = logging.getLogger(__name__)


def _segment_to_chunk(
    llm_service: LLMServiceBase,
    segment: FileSegment,
    full_content: str,
    file_path: str,
    llm_model: str,
) -> str:

    # NOTE: For markdown files we could embed directly without LLM summarization.
    #       Just split on ## headers.

    logger.info(
        "Analyzing segment %s in file %s...", segment.content.split("\n")[0], file_path
    )

    messages = [
        {"role": "system", "content": "You are an expert at describing code."},
        {
            "role": "user",
            "content": f"""In the context of the following file:
<File Path>{file_path}</File Path>
<FileContent>
{full_content}
</FileContent>
Please describe the purpose following {segment.type}:
<Segment>
<Line Start>{segment.line_start}</Line Start>
<Content>
{segment.content}
</Content>
<Line End>{segment.line_end}</Line End>
</Segment>
If this is a function or class, please describe what it does and how it interacts with the application.
If it is a text paragraph, explain what it covers.
Focus on the key aspects of the text or code.
Write a succint summary.
Return the summary only without any additional comments.
Start with, e.g.,
This {segment.type} is ...
""",
        },
    ]

    response = llm_service.generate_response(messages, llm_model)

    logger.info("Generated summary for segment in file %s: %s", file_path, response)

    return response


class DocEmbedder:
    def __init__(
        self,
        doc_provider: DocProviderBase,
        vector_db: VectorDbBase,
        llm_service: LLMServiceBase,
        llm_model: str,
        debounce_seconds: int = 10,
    ) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db
        self._llm_service = llm_service
        self._llm_model = llm_model
        self._debounce_seconds = debounce_seconds

    def embed_codebase(self) -> None:
        """ Embeds the codebase and prepares it for vector search."""

        logger.info("Computing deltas...")

        chunks_ids_to_remove, files_to_update = DeltaComputer(
            self._doc_provider, self._vector_db, self._debounce_seconds
        ).compute_deltas()

        logger.info(
            f"Detected {len(chunks_ids_to_remove)} chunks to delete from vector database."
        )
        logger.info(f"Detected {len(files_to_update)} files to process.")

        if chunks_ids_to_remove:
            logger.info(
                f"Deleting {len(chunks_ids_to_remove)} chunks from vector database."
            )
            self._vector_db.delete_chunks(list(chunks_ids_to_remove))

        logger.info(f"Processing {len(files_to_update)} files...")

        num_processed = 0
        num_skipped = 0

        for i, file in enumerate(files_to_update):
            logger.info(f"Processing file '{file}' ({i + 1}/{len(files_to_update)})...")
            ext = file.split(".")[-1]
            splitter = DocSplitterFactory.create(ext)
            if splitter is None:
                # NOTE: We could alternatively embed the full file as a fallback.
                #       As long as we trust filter system.
                logger.warning(
                    f"Cannot embed file at path '{file}'. No splitter implemented for this file extension."
                )
                num_skipped += 1
                continue
            doc = self._doc_provider.get_content(file)
            segments = splitter.split_file(doc.content)
            chunks = []
            for segment in segments:
                summary = _segment_to_chunk(
                    self._llm_service, segment, doc.content, file, self._llm_model
                )
                chunks.append(
                    Chunk(
                        id=uuid4(),
                        modified_at=doc.modified_at,
                        content=summary,
                        file_path=file,
                        line_start=segment.line_start,
                        line_end=segment.line_end,
                        raw_code=segment.content,
                        file_sha256_checksum=doc.sha256_checksum,
                    )
                )
            if not chunks:
                logger.warning(
                    f"No chunks generated for file '{file}'. Skipping embedding for this file."
                )
                num_skipped += 1
                continue
            logger.info(f"Saving {len(chunks)} chunks to vector database.")
            self._vector_db.add_chunks(chunks)
            num_processed += 1
            logger.info(f"Successfully embedded file: '{file}' ({i + 1}/{len(files_to_update)}).")

        if num_processed > 0:
            logger.info(f"Successfully embedded {num_processed} files.")
        if num_skipped > 0:
            logger.warning(f"Skipped processing {num_skipped} files.")
