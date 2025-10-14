"""
Field-based weighted search engine

A simpler alternative to BM25 that focuses on field-level matching
with explicit weights and avoids document length bias.

## Algorithm Design

This search engine implements a three-layer scoring system to prevent score explosion
and ensure relevant results:

### Layer 1: Match Quality Scoring
For each token-field match, we assign a base score based on match quality:
- Exact match: weight × 3.0 (e.g., field value "projects" == query "projects")
- Word boundary match: weight × 2.0 (e.g., "list projects" matches query "projects" as complete word)
- Partial match: weight × 1.0 (e.g., "project_list" contains query "project")

### Layer 2: Intra-field Token Decay (Harmonic Series)
When multiple query tokens match within the same field, we apply diminishing returns:
- 1st token: 100% of score
- 2nd token: 50% of score (1/2)
- 3rd token: 33% of score (1/3)
- 4th token: 25% of score (1/4)

This prevents long descriptions from accumulating excessive scores by matching many tokens.

### Layer 3: Per-field Logarithmic Dampening
After calculating field scores, we apply logarithmic dampening based on field type:
- Description fields (description, param_desc): log(1 + score) × 5 (stronger dampening)
- Identifier fields (service, operation, tag, path, etc.): log(1 + score) × 10 (lighter dampening)

This prevents any single field from dominating the final score, especially verbose fields.

### Final Score Calculation
- Sum all dampened field scores
- Add diversity bonus: sqrt(matched_field_types) × 3
  (rewards matching across multiple field types)

## Problem Scenarios This Solves

### Scenario 1: Keyword Repetition
Query: "projects"
Without dampening:
- Endpoint A: service="projects"(90) + tag="projects"(90) + path="/projects"(60) +
              description="manage projects"(20) = 260 points
- Endpoint B: service="users"(0) + operation="get_user_projects"(60) = 60 points

With our algorithm:
- Endpoint A: log(91)×10 + log(91)×10 + log(61)×10 + log(21)×5 = 45.5+45.5+40.2+15.2 = 146.4
- Endpoint B: log(61)×10 = 40.2

Still favors A but with reasonable margin, not 4x difference.

### Scenario 2: Long Description Domination
Query: "create user project pipeline"
Without dampening:
- Endpoint A: description contains all 4 words = 20×4 = 80 points
- Endpoint B: operation="create_pipeline" = 30×2 = 60 points

With our algorithm:
- Endpoint A: (20 + 20/2 + 20/3 + 20/4) = 41.7 → log(42.7)×5 = 18.6 points
- Endpoint B: 30×2 = 60 → log(61)×10 = 40.2 points

Now B correctly ranks higher as it's more specific.

### Scenario 3: Exact Service Name Match
Query: "projects"
- Service name exactly "projects": 30×3=90 → log(91)×10 = 45.5 points
This ensures exact matches still get high scores despite dampening.

## Weight Configuration

Weights should be configured based on field importance:
- High (30): service, operation, tag, path - core identifiers
- Medium (20): summary, description - contextual information
- Low (5): method, param - auxiliary information
- Minimal (1-2): param_desc, body_field - verbose/detailed fields

The weights are passed during document indexing, allowing different OpenAPI
implementations to customize based on their documentation structure.
"""

import math
import re
from typing import List, Tuple


class FieldSearchEngine:
    """
    Simple field-based search engine with weighted scoring
    Compatible with BM25SearchEngine interface
    """

    def __init__(self, **kwargs):
        """Initialize the search engine (kwargs for compatibility with BM25SearchEngine)"""
        self.documents = []
        self.corpus_metadata = None

    def build_index(self, documents: List[Tuple[List[Tuple[str, str, int]], str]]):
        """
        Build index from documents

        Args:
            documents: List of (fields, doc_id) tuples
                      fields: List of (field_key, field_value, weight) tuples
                              weight is used as field priority
                      doc_id: Document identifier string
        """
        self.documents = []
        self.corpus_metadata = []

        for fields, doc_id in documents:
            # Store document with structured fields and their weights
            doc_fields = {}
            field_weights = {}

            for field_key, field_value, weight in fields:
                if field_value:
                    # Group values by field type
                    if field_key not in doc_fields:
                        doc_fields[field_key] = []
                        field_weights[field_key] = weight
                    doc_fields[field_key].append(field_value.lower())

                    # Use the highest weight if multiple values for same field
                    if weight > field_weights.get(field_key, 0):
                        field_weights[field_key] = weight

            self.documents.append(
                {"id": doc_id, "fields": doc_fields, "weights": field_weights}
            )
            self.corpus_metadata.append(doc_id)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[float, str]]:
        """
        Search documents with field-weighted scoring and logarithmic dampening

        Args:
            query: Search query string
            top_k: Number of top results to return

        Returns:
            List of (score, doc_id) tuples sorted by score descending
        """
        if not self.documents:
            return []

        # Tokenize query into words
        query_tokens = query.lower().split()

        results = []

        for doc in self.documents:
            # Track scores by field type to apply per-field dampening
            field_scores = {}
            matched_field_types = set()

            # Check each field type
            for field_type, field_values in doc["fields"].items():
                # Get weight from document's field weights
                field_weight = doc["weights"].get(field_type, 1.0)

                # Track tokens matched in this field
                field_token_scores = []
                matched_tokens = set()

                # For each query token
                for token in query_tokens:
                    # Check if token appears in any value of this field
                    best_match_score = 0

                    for value in field_values:
                        if (
                            self._match_token(token, value)
                            and token not in matched_tokens
                        ):
                            # Calculate match quality
                            match_score = 0

                            # Exact match gets highest score
                            if value == token:
                                match_score = 3.0
                            # Word boundary match (complete word)
                            elif re.search(r"\b" + re.escape(token) + r"\b", value):
                                match_score = 2.0
                            # Partial match gets base score
                            else:
                                match_score = 1.0

                            best_match_score = max(best_match_score, match_score)

                    if best_match_score > 0:
                        matched_tokens.add(token)
                        field_token_scores.append(field_weight * best_match_score)
                        matched_field_types.add(field_type)

                # Apply diminishing returns for multiple tokens in same field
                if field_token_scores:
                    # Sort scores in descending order
                    field_token_scores.sort(reverse=True)

                    # Apply decay: 1st token 100%, 2nd 50%, 3rd 33%, etc.
                    field_total = 0
                    for i, token_score in enumerate(field_token_scores):
                        field_total += token_score / (i + 1)

                    # Apply logarithmic dampening per field to prevent single field domination
                    # This prevents description or other verbose fields from dominating
                    if field_type in ["description", "param_desc"]:
                        # Stronger dampening for description fields
                        field_scores[field_type] = math.log(1 + field_total) * 5
                    else:
                        # Lighter dampening for identifier fields
                        field_scores[field_type] = math.log(1 + field_total) * 10

            # Calculate final score
            if field_scores:
                # Sum all field scores (already dampened per field)
                total_score = sum(field_scores.values())

                # Add diversity bonus for matching multiple field types
                diversity_bonus = math.sqrt(len(matched_field_types)) * 3

                final_score = total_score + diversity_bonus
                results.append((final_score, doc["id"]))

        # Sort by score descending and return top k
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    def _match_token(self, token: str, text: str) -> bool:
        """Check if token matches in text"""
        return token in text
