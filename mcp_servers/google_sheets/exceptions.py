# Error class for retryable errors
class RetryableToolError(Exception):
    def __init__(self, message: str, additional_prompt_content: str = "", retry_after_ms: int = 1000, developer_message: str = ""):
        super().__init__(message)
        self.additional_prompt_content = additional_prompt_content
        self.retry_after_ms = retry_after_ms
        self.developer_message = developer_message

# Error class for tool execution errors
class ToolExecutionError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
