import logging
from typing import List
from uuid import uuid4

from pydantic import BaseModel

from codeembed.delta_computer.delta_computer import DeltaComputer
from codeembed.doc_provider.base import DocProviderBase
from codeembed.doc_splitters.generic_splitter import FileSplitter
from codeembed.doc_splitters.models import FileSegment
from codeembed.graph_db.base import GraphDbBase
from codeembed.graph_db.models import Edge
from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import ChatMessage
from codeembed.vector_db.base import VectorDbBase
from codeembed.vector_db.models import Chunk

logger = logging.getLogger(__name__)


def _summarize_chunk_with_llm(
    llm_service: LLMServiceBase,
    segment: FileSegment,
    full_content: str,
    file_path: str,
    llm_model: str,
) -> str:

    # NOTE: For markdown files we could embed directly without LLM summarization.
    #       Just split on ## headers.

    logger.info(
        "Summarizing segment %s in file %s:%d-%d...",
        segment.content.split("\n")[0],
        file_path,
        segment.line_start,
        segment.line_end,
    )

    messages: List[ChatMessage] = [
        {"role": "system", "content": "You are an expert at describing code."},
        {
            "role": "user",
            "content": f"""In the context of the following file:
<File Path>{file_path}</File Path>
<FileContent>
{full_content}
</FileContent>
Please describe the purpose following code/text segment:
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
This <segment type> is ...
""",
        },
    ]

    result = llm_service.generate_response(messages, llm_model, max_tokens=1024, temperature=0.3)

    logger.info("Generated summary for segment in file %s. Length: %d", file_path, len(result.response))

    return result.response


class _Edge(BaseModel):
    source: str
    relation: str
    target: str


class _GraphOutput(BaseModel):
    edges: List[_Edge]  # source, relation, target


def _normalize_edge(edge: _Edge) -> _Edge:
    return _Edge(
        source=edge.source.strip(),
        relation=edge.relation.strip().upper().replace(" ", "_"),
        target=edge.target.strip(),
    )


def _find_graph_relations_with_llm(
    llm_service: LLMServiceBase,
    segment: FileSegment,
    full_content: str,
    file_path: str,
    llm_model: str,
    summary: str,
) -> List[_Edge]:

    logger.info(
        "Extracting graph relations for segment %s in file %s:%d-%d...",
        segment.content.split("\n")[0],
        file_path,
        segment.line_start,
        segment.line_end,
    )

    messages: List[ChatMessage] = [
        {
            "role": "system",
            "content": (
                "You extract relationships from code or text and return structured graph edges.\n\n"
                "Node ID format rules — follow these exactly:\n"
                "- Class method:       ClassName.method_name         e.g. AuthService.login\n"
                "- Class:              ClassName                     e.g. AuthService\n"
                "- Module-level func:  function_name                 e.g. jwt_decode\n"
                "- Module/file:        module_name                   e.g. utils, auth.helpers\n"
                "- Concept/topic:      lowercase_snake_case          e.g. user_authentication\n\n"
                "Relation format rules:\n"
                "- UPPER_SNAKE_CASE always                           e.g. CALLS, IMPORTS, EXTENDS, IMPLEMENTS, USES\n\n"
                "Other rules:\n"
                "- Only output relations explicitly present in the code or text\n"
                "- Use full file context to resolve ambiguous references\n"
                "- Do NOT invent nodes or relations\n"
                "- Ignore trivial variable assignments and local-only references\n"
                "- Node IDs must be real code symbols (class names, function names, module paths) — NEVER string "
                "literals, single letters, placeholder values, or test input data\n"
            ),
        },
        {
            "role": "user",
            "content": f"""
<FilePath>{file_path}</FilePath>

<FileSummary>
{summary}
</FileSummary>

<FullFileContent>
{full_content}
</FullFileContent>

<Segment lines="{segment.line_start}-{segment.line_end}">
{segment.content}
</Segment>

Extract graph relations from the Segment only (use FullFileContent for context/disambiguation).

Examples of correct output:
  AuthService.login CALLS UserRepository.find_by_email
  AuthService.login CALLS JwtService.sign
  AuthService IMPORTS jwt_decode
  UserRepository EXTENDS BaseRepository
  DocEmbedder.embed_codebase USES FileSplitter

Return STRICT JSON:
{{
  "edges": [
    {{
      "source": "...",
      "relation": "...",
      "target": "..."
    }}
  ]
}}
""",
        },
    ]

    try:
        result = llm_service.generate_structured_output(
            messages=messages,
            llm_model=llm_model,
            output_format=_GraphOutput,
            max_tokens=512,
            temperature=0.1,
        )
    except Exception as e:
        logger.warning(
            "Failed to extract graph relations for segment in '%s' (lines %s-%s): %s",
            file_path,
            segment.line_start,
            segment.line_end,
            e,
        )
        return []

    logger.info("Extracted %d graph edges for segment in file %s.", len(result.data.edges), file_path)

    return [_normalize_edge(edge) for edge in result.data.edges]


class DocEmbedder:
    def __init__(
        self,
        doc_provider: DocProviderBase,
        vector_db: VectorDbBase,
        graph_db: GraphDbBase,
        llm_service: LLMServiceBase,
        llm_model: str,
        debounce_seconds: int = 10,
    ) -> None:
        self._doc_provider = doc_provider
        self._vector_db = vector_db
        self._graph_db = graph_db
        self._llm_service = llm_service
        self._llm_model = llm_model
        self._debounce_seconds = debounce_seconds

    def embed_codebase(self) -> None:
        """Embeds the codebase and prepares it for vector search."""

        logger.info("Computing deltas...")

        chunks_ids_to_remove, files_to_update, file_paths_to_delete = DeltaComputer(
            self._doc_provider, self._vector_db, self._debounce_seconds
        ).compute_deltas()

        logger.info(f"Detected {len(chunks_ids_to_remove)} chunks to delete from vector database.")
        logger.info(f"Detected {len(files_to_update)} files to process.")
        logger.info(f"Detected {len(file_paths_to_delete)} files to delete.")

        if chunks_ids_to_remove:
            logger.info(f"Deleting {len(chunks_ids_to_remove)} chunks from vector database.")
            self._vector_db.delete_chunks(list(chunks_ids_to_remove))

        for file_path in files_to_update | file_paths_to_delete:
            logger.info(f"Deleting edges for file '{file_path}' from graph database.")
            self._graph_db.delete_edges_by_file_path(file_path)

        logger.info(f"Processing {len(files_to_update)} files...")

        num_processed = 0
        num_skipped = 0

        splitter = FileSplitter()

        # TODO: Add multi-threading.

        for i, file in enumerate(files_to_update):
            logger.info(f"Processing file '{file}' ({i + 1}/{len(files_to_update)})...")
            doc = self._doc_provider.get_content(file)
            segments = splitter.split_file(doc.content, file)
            chunks = []
            edges: List[Edge] = []
            for segment in segments:
                summary = _summarize_chunk_with_llm(self._llm_service, segment, doc.content, file, self._llm_model)

                _edges = _find_graph_relations_with_llm(
                    self._llm_service, segment, doc.content, file, self._llm_model, summary
                )

                chunk = Chunk(
                    id=uuid4(),
                    modified_at=doc.modified_at,
                    content=summary,
                    file_path=file,
                    line_start=segment.line_start,
                    line_end=segment.line_end,
                    raw_code=segment.content,
                    file_sha256_checksum=doc.sha256_checksum,
                    graph_node_ids=[edge.source for edge in _edges],
                )

                chunks.append(chunk)

                edges.extend(
                    [
                        Edge(
                            source=edge.source,
                            relation=edge.relation,
                            target=edge.target,
                            file_path=file,
                            chunk_id=chunk.id,
                            properties={
                                "line_start": segment.line_start,
                                "line_end": segment.line_end,
                                "modified_at": doc.modified_at.isoformat(),
                                "file_sha256_checksum": doc.sha256_checksum,
                            },
                        )
                        for edge in _edges
                    ]
                )
            if not chunks:
                logger.warning(f"No chunks generated for file '{file}'. Skipping embedding for this file.")
                num_skipped += 1
                continue
            logger.info(f"Saving {len(edges)} edges to graph database.")
            for edge in edges:
                self._graph_db.add_edge(edge)
            logger.info(f"Saving {len(chunks)} chunks to vector database.")
            self._vector_db.add_chunks(chunks)
            num_processed += 1
            logger.info(f"Successfully embedded file: '{file}' ({i + 1}/{len(files_to_update)}).")

        if num_processed > 0:
            logger.info(f"Successfully embedded {num_processed} files.")
        if num_skipped > 0:
            logger.warning(f"Skipped processing {num_skipped} files.")
