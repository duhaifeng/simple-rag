"""BM25 Engine — authentic Okapi BM25 with inverted index.

Implements:
- Inverted index: term -> list of (doc_internal_id, term_frequency)
- Per-document length (dl) and corpus average (avgdl)
- Okapi BM25 scoring with configurable k1, b, k3 (query-tf)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from simple_rag.retrieval.bm25.tokenizer import Tokenizer, JiebaTokenizer


@dataclass
class _DocRecord:
    """Internal record for an indexed document/chunk."""

    chunk_id: str
    doc_id: str
    text: str
    dl: int  # document length in tokens
    metadata: dict = field(default_factory=dict)


class BM25Engine:
    """In-memory Okapi BM25 engine with inverted index.

    Scoring formula (per query term t):
        score(t, D) = idf(t) * ( tf(t,D) * (k1 + 1) ) / ( tf(t,D) + k1 * (1 - b + b * dl/avgdl) )

    Where:
        idf(t) = log( (N - df(t) + 0.5) / (df(t) + 0.5) + 1 )
        N      = total number of documents
        df(t)  = number of documents containing term t
        tf(t,D)= term frequency of t in document D
        dl     = document length (in tokens)
        avgdl  = average document length

    Optional query-tf weighting (when k3 > 0):
        query_weight(t) = ( (k3 + 1) * qtf(t) ) / ( k3 + qtf(t) )
    """

    def __init__(
        self,
        tokenizer: Tokenizer | None = None,
        k1: float = 1.5,
        b: float = 0.75,
        k3: float = 0.0,
    ):
        self._tokenizer = tokenizer or JiebaTokenizer()
        self.k1 = k1
        self.b = b
        self.k3 = k3

        # Corpus state
        self._docs: list[_DocRecord] = []
        self._inverted_index: dict[str, list[tuple[int, int]]] = {}  # term -> [(doc_idx, tf)]
        self._df: dict[str, int] = {}  # term -> document frequency
        self._total_dl: int = 0
        self._N: int = 0

    # ---- Indexing ----

    def add_documents(
        self,
        chunks: list[dict],
    ) -> int:
        """Add documents/chunks to the index.

        Each chunk dict should have: chunk_id, doc_id, text, and optional metadata.
        Returns number of documents added.
        """
        count = 0
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            doc_id = chunk.get("doc_id", "")
            text = chunk.get("text", "")
            metadata = chunk.get("metadata", {})

            tokens = self._tokenizer.tokenize(text)
            dl = len(tokens)
            doc_idx = len(self._docs)

            self._docs.append(_DocRecord(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text=text,
                dl=dl,
                metadata=metadata,
            ))

            # Build term frequencies for this document
            tf_map: dict[str, int] = {}
            for token in tokens:
                tf_map[token] = tf_map.get(token, 0) + 1

            # Update inverted index and df
            for term, tf in tf_map.items():
                if term not in self._inverted_index:
                    self._inverted_index[term] = []
                self._inverted_index[term].append((doc_idx, tf))
                self._df[term] = self._df.get(term, 0) + 1

            self._total_dl += dl
            self._N += 1
            count += 1

        return count

    def clear(self) -> None:
        """Clear the entire index."""
        self._docs.clear()
        self._inverted_index.clear()
        self._df.clear()
        self._total_dl = 0
        self._N = 0

    # ---- Search ----

    def search(self, query: str, top_k: int = 200) -> list[dict]:
        """Search the index with BM25 scoring.

        Returns:
            list of dicts with keys: chunk_id, doc_id, text, score, metadata.
            Sorted by score descending, length <= top_k.
        """
        if self._N == 0:
            return []

        query_tokens = self._tokenizer.tokenize(query)
        if not query_tokens:
            return []

        avgdl = self._total_dl / self._N

        # Query term frequencies (for k3 weighting)
        qtf_map: dict[str, int] = {}
        for t in query_tokens:
            qtf_map[t] = qtf_map.get(t, 0) + 1

        # Accumulate scores
        scores: dict[int, float] = {}

        for term in set(query_tokens):
            if term not in self._inverted_index:
                continue

            df = self._df[term]
            # IDF: log((N - df + 0.5) / (df + 0.5) + 1)
            idf = math.log((self._N - df + 0.5) / (df + 0.5) + 1.0)

            # Query-tf weight
            if self.k3 > 0:
                qtf = qtf_map.get(term, 1)
                query_weight = ((self.k3 + 1) * qtf) / (self.k3 + qtf)
            else:
                query_weight = 1.0

            for doc_idx, tf in self._inverted_index[term]:
                dl = self._docs[doc_idx].dl
                # TF saturation
                tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / avgdl))
                score = idf * tf_component * query_weight
                scores[doc_idx] = scores.get(doc_idx, 0.0) + score

        # Sort and return top_k
        sorted_doc_indices = sorted(scores, key=lambda idx: scores[idx], reverse=True)[:top_k]

        return [
            {
                "chunk_id": self._docs[idx].chunk_id,
                "doc_id": self._docs[idx].doc_id,
                "text": self._docs[idx].text,
                "score": scores[idx],
                "metadata": self._docs[idx].metadata,
            }
            for idx in sorted_doc_indices
        ]

    # ---- Stats ----

    @property
    def num_documents(self) -> int:
        return self._N

    @property
    def num_terms(self) -> int:
        return len(self._inverted_index)

    @property
    def avg_document_length(self) -> float:
        return self._total_dl / self._N if self._N > 0 else 0.0
