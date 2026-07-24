from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class SourceCitation(BaseModel):
    title: str
    source_type: str
    source_url: str
    author: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    confidence: float  # 0.0 - 1.0, derived from retrieval similarity
    access_denied: bool  # true when the pre-filter returned zero eligible chunks


class SMEEntry(BaseModel):
    author: str
    domains: list[str]
    document_count: int
