class ToolExecutionError(Exception):
    def __init__(self, message: str, developer_message: str = ""):
        super().__init__(message)
        self.developer_message = developer_message


class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message

class AuthenticationError(ToolExecutionError):
    def __init__(self, message: str, developer_message: str = ""):
        super().__init__(message, developer_message)


class TokenExpiredError(AuthenticationError):
    def __init__(self, message: str = "OAuth token has expired", developer_message: str = ""):
        super().__init__(message, developer_message)


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "OAuth token is invalid", developer_message: str = ""):
        super().__init__(message, developer_message) 