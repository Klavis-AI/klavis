"""
BM25+ based search utility with field-level scoring

This implementation flattens document fields into separate documents for independent scoring,
then aggregates scores by original document ID with field weights.

Algorithm:
1. Each field becomes a separate document: "original_id:field_key" -> field_value
2. BM25 scores each field independently
3. Final score = sum(field_score * field_weight) for all fields of same original_id

Installation:
    pip install "bm25s"
    pip install PyStemmer
"""

from collections import defaultdict
from typing import List, Tuple

import bm25s
import Stemmer


class BM25SearchEngine:
    """
    Field-aware BM25+ search engine that scores each field independently
    """

    def __init__(self, use_stemmer: bool = True):
        """
        Initialize the BM25+ search engine

        Args:
            use_stemmer: Whether to use stemming for better search results
        """
        self.stemmer = Stemmer.Stemmer("english") if use_stemmer else None
        self.retriever = None
        # Maps flattened_doc_id -> (original_doc_id, field_key, field_weight)
        self.corpus_metadata = None
        # Maps original_doc_id -> [(field_key, weight), ...]
        self.doc_field_weights = None

    def build_index(self, documents: List[Tuple[List[Tuple[str, str, int]], str]]):
        """
        Build BM25 index from documents by flattening fields into separate documents

        Args:
            documents: List of (fields, doc_id) tuples
                      fields: List of (field_key, field_value, weight) tuples
                      doc_id: Document identifier string

        Example:
            documents = [
                (
                    [
                        ("service", "projects", 30),
                        ("operation", "create_project", 30),
                        ("description", "Creates a new project", 20),
                    ],
                    "projects:create_project"
                ),
            ]

        This creates separate BM25 documents:
            - "projects:create_project:service" -> "projects"
            - "projects:create_project:operation" -> "create_project"
            - "projects:create_project:description" -> "Creates a new project"
        """
        corpus = []
        self.corpus_metadata = []
        self.doc_field_weights = defaultdict(list)

        for fields, original_doc_id in documents:
            for field_key, field_value, weight in fields:
                if field_value and weight > 0:
                    # Preprocess field value for better tokenization
                    processed_value = self._preprocess_field_value(field_value.strip())
                    corpus.append(processed_value)

                    # Store metadata: flattened_id -> (original_id, field_key, weight)
                    self.corpus_metadata.append((original_doc_id, field_key, weight))

                    # Store field weights by original document
                    self.doc_field_weights[original_doc_id].append((field_key, weight))

        if not corpus:
            raise ValueError("No documents to index")

        # Tokenize corpus (each field value separately)
        corpus_tokens = bm25s.tokenize(
            corpus,
            stopwords=[],  # Disable stopwords for better field matching
            show_progress=False,
        )

        # Create and index BM25+ retriever
        self.retriever = bm25s.BM25(method="bm25+")
        self.retriever.index(corpus_tokens, show_progress=False)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[float, str]]:
        """
        Search indexed documents with field-level scoring and weighted aggregation

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of (score, doc_id) tuples sorted by score descending

        Algorithm:
            1. Search all flattened field documents
            2. Group results by original document ID
            3. Calculate weighted sum: score = sum(field_score * field_weight)
            4. Return top_k results by final weighted score
        """
        if self.retriever is None or self.corpus_metadata is None:
            raise ValueError("No documents indexed. Call build_index() first.")

        # Tokenize query (matching build_index settings)
        query_tokens = bm25s.tokenize(
            query,
            stopwords=[],  # Disable stopwords to match build_index
            show_progress=False,
        )

        # Search all flattened documents to ensure complete field aggregation
        # We need all matching fields for accurate document scoring
        search_k = len(self.corpus_metadata)
        doc_indices, scores = self.retriever.retrieve(
            query_tokens, k=search_k, show_progress=False
        )

        # Aggregate scores by original document ID
        doc_scores = defaultdict(float)

        for i in range(doc_indices.shape[1]):
            idx = doc_indices[0, i]
            field_score = scores[0, i]

            if idx < len(self.corpus_metadata):
                original_doc_id, _, field_weight = self.corpus_metadata[idx]

                # Add weighted field score to document total
                weighted_score = float(field_score) * field_weight
                doc_scores[original_doc_id] += weighted_score

        # Sort by aggregated score and return top k
        sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top_k results as (score, doc_id) tuples
        return [(score, doc_id) for doc_id, score in sorted_results[:top_k]]

    def _preprocess_field_value(self, value: str) -> str:
        """
        Preprocess field values to improve tokenization

        Converts underscore_separated and camelCase text to space-separated words
        for better BM25 matching.

        Examples:
            "create_project" -> "create project"
            "getUserProjects" -> "get User Projects"
            "/api/v1/projects" -> "/api/v1/projects"
        """
        import re

        # Replace underscores with spaces
        value = value.replace("_", " ")

        # Replace hyphens with spaces
        value = value.replace("-", " ")

        # Split camelCase: insert space before uppercase letters
        # But preserve existing spaces and special characters
        value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)

        # Clean up multiple spaces
        value = re.sub(r"\s+", " ", value).strip()

        return value
