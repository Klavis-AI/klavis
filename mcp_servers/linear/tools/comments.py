import logging
from typing import Any, Dict
from .base import make_graphql_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_comments(issue_id: str) -> Dict[str, Any]:
    """Get comments for a specific issue."""
    logger.info(f"Executing tool: get_comments with issue_id: {issue_id}")
    try:
        query = """
        query IssueComments($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            comments {
              nodes {
                id
                body
                user {
                  id
                  name
                  email
                }
                createdAt
                updatedAt
                url
              }
            }
          }
        }
        """
        variables = {"id": issue_id}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_comments: {e}")
        raise e

async def create_comment(issue_id: str, body: str) -> Dict[str, Any]:
    """Create a comment on an issue."""
    logger.info(f"Executing tool: create_comment on issue: {issue_id}")
    try:
        query = """
        mutation CommentCreate($input: CommentCreateInput!) {
          commentCreate(input: $input) {
            success
            comment {
              id
              body
              user {
                id
                name
                email
              }
              issue {
                id
                identifier
                title
              }
              createdAt
              url
            }
          }
        }
        """
        
        input_data = {
            "issueId": issue_id,
            "body": body
        }
        
        variables = {"input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool create_comment: {e}")
        raise e

async def update_comment(comment_id: str, body: str) -> Dict[str, Any]:
    """Update an existing comment."""
    logger.info(f"Executing tool: update_comment with comment_id: {comment_id}")
    try:
        query = """
        mutation CommentUpdate($id: String!, $input: CommentUpdateInput!) {
          commentUpdate(id: $id, input: $input) {
            success
            comment {
              id
              body
              user {
                id
                name
                email
              }
              issue {
                id
                identifier
                title
              }
              updatedAt
              url
            }
          }
        }
        """
        
        input_data = {"body": body}
        variables = {"id": comment_id, "input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool update_comment: {e}")
        raise e 