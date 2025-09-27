import sqlparse
from sqlparse.sql import Token, TokenList
from sqlparse.tokens import Keyword, DML, DDL
from typing import Dict, List, Set, Tuple


class SQLWriteDetector:
    def __init__(self):
        # Define sets of keywords that indicate write operations
        self.dml_write_keywords = {"INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE"}

        self.ddl_keywords = {"CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME"}

        self.dcl_keywords = {"GRANT", "REVOKE"}

        # Combine all write keywords
        self.write_keywords = self.dml_write_keywords | self.ddl_keywords | self.dcl_keywords

    def analyze_query(self, sql_query: str) -> Dict:
        """
        Analyze a SQL query to determine if it contains write operations.

        Args:
            sql_query: The SQL query string to analyze

        Returns:
            Dictionary containing analysis results
        """
        # Parse the SQL query
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return {"contains_write": False, "write_operations": set(), "has_cte_write": False}

        # Initialize result tracking
        found_operations = set()
        has_cte_write = False

        # Analyze each statement in the query
        for statement in parsed:
            # Check for write operations in CTEs (WITH clauses)
            if self._has_cte(statement):
                cte_write = self._analyze_cte(statement)
                if cte_write:
                    has_cte_write = True
                    found_operations.add("CTE_WRITE")

            # Analyze the main query
            operations = self._find_write_operations(statement)
            found_operations.update(operations)

        return {
            "contains_write": bool(found_operations) or has_cte_write,
            "write_operations": found_operations,
            "has_cte_write": has_cte_write,
        }

    def _has_cte(self, statement: TokenList) -> bool:
        """Check if the statement has a WITH clause."""
        return any(token.is_keyword and token.normalized == "WITH" for token in statement.tokens)

    def _analyze_cte(self, statement: TokenList) -> bool:
        """
        Analyze CTEs (WITH clauses) for write operations.
        Returns True if any CTE contains a write operation.
        """
        in_cte = False
        for token in statement.tokens:
            if token.is_keyword and token.normalized == "WITH":
                in_cte = True
            elif in_cte:
                if any(write_kw in token.normalized for write_kw in self.write_keywords):
                    return True
        return False

    def _find_write_operations(self, statement: TokenList) -> Set[str]:
        """
        Find all write operations in a statement.
        Returns a set of found write operation keywords.
        """
        operations = set()

        for token in statement.tokens:
            # Skip comments and whitespace
            if token.is_whitespace or token.ttype in (sqlparse.tokens.Comment,):
                continue

            # Check if token is a keyword
            if token.ttype in (Keyword, DML, DDL):
                normalized = token.normalized.upper()
                if normalized in self.write_keywords:
                    operations.add(normalized)

            # Recursively check child tokens
            if isinstance(token, TokenList):
                child_ops = self._find_write_operations(token)
                operations.update(child_ops)

        return operations
