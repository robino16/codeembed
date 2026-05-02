import logging
from uuid import uuid4

from src.delta_computer.delta_computer import DeltaComputer
from src.doc_provider.base import DocProviderBase
from src.doc_splitters.factory import DocSplitterFactory
from src.doc_splitters.models import FileSegment
from src.llm.base import LLMServiceBase
from src.utils.time_utils import utc_now
from src.vector_db.base import VectorDbBase
from src.vector_db.models import Chunk

logger = logging.getLogger(__name__)


def _segment_to_chunk(
    llm_service: LLMServiceBase,
    segment: FileSegment,
    full_content: str,
    file_path: str,
    llm_model: str,
) -> str:

    # NOTE: Perhaps we could use the segment type condionally?
    #       For documentation (like markdown) just embed it directly?

    # To ensure up to date file,
    # We could read it's content again here right before embedding.
    # To ensure we get a updated version.

    # If the file was updated within e.g., last 10 seconds, we should have a debounce and wait to embed it again.

    messages = [
        {"role": "system", "content": "You are an expert at describing code."},
        {
            "role": "user",
            "content": f"""In the context of the following file:
<File Path>{file_path}</File Path>
<FileContent/>
{full_content}
<FileContent>
Please describe the purpose following {segment.type}:
<Segment>
<Line Start>{segment.line_start}</Line Start>
<Title>
{segment.content.split("\n")[0]}
</Title>
<Line End>{segment.line_end}</Line End>
</Segment>
If this is a function or class, please describe what it does and how it interacts with the application.
If it is a text paragraph, explain what it covers.
Focus on the key aspects of the text or code.
Write a succint summary.
Return the summary only without any additional comments.
""",
        },
    ]

    response = llm_service.generate_response(messages, llm_model)

    return response


class DocEmbedder:
    def ___init__(
        self,
        doc_provider: DocProviderBase,
        vector_db: VectorDbBase,
        llm_service: LLMServiceBase,
        llm_model: str,
    ) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db
        self._llm_service = llm_service
        self._llm_model = llm_model

    def embed_codebase(self) -> None:
        chunks_ids_to_remove, files_to_update = DeltaComputer(
            self._doc_provider, self._vector_db
        ).compute_deltas()

        logger.info(
            f"Detected {len(chunks_ids_to_remove)} chunks to delete from vector database."
        )
        logger.info(f"Detected {len(files_to_update)} files to reprocess.")

        self._vector_db.delete_chunks(list(chunks_ids_to_remove))

        for file in files_to_update:
            ext = file.split(".")[-1]
            splitter = DocSplitterFactory.create(ext)
            if splitter is None:
                # We could alternatively embed the full file as a fallback.
                # As long as we trust filter system.
                logger.warning(
                    f"Cannot embed file at path '{file}'. No splitter implemented for this file extension."
                )
                continue
            content = self._doc_provider.get_content(file)
            segments = splitter.split_file(content)
            chunks = []
            for segment in segments:
                summary = _segment_to_chunk(
                    self._llm_service, segment, content, file, self._llm_model
                )
                chunks.append(
                    Chunk(
                        id=uuid4(),
                        modified_at=utc_now(),  # TODO: Use actual modified_date of file.
                        content=summary,
                        file_path=file,
                        line_start=segment.line_start,
                        line_end=segment.line_end,
                    )
                )
            self._vector_db.add_chunks(chunks)
