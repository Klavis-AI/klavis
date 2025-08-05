import traceback


class QuickBooksError(Exception):
    """
    A custom error wrapper that preserves the original traceback and allows custom error messages.
    """

    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception
        if original_exception is not None:
            self.traceback = traceback.format_exc()
        else:
            self.traceback = None

    def __str__(self):
        base = f"QuickBooksError: {self.message}"
        if self.original_exception:
            base += f"\nCaused by: {repr(self.original_exception)}"
        if self.traceback:
            base += f"\nTraceback (most recent call last):\n{self.traceback}"
        return base
