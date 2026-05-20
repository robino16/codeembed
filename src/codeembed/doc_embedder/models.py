from typing import List

from pydantic import BaseModel


class GraphAnalysisResultEdge(BaseModel):
    source: str
    relation: str
    target: str


class GraphAnalysisResult(BaseModel):
    edges: List[GraphAnalysisResultEdge]
