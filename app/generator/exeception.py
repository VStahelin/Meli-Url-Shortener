class ShortenUrlDeletionFailed(Exception):
    """
    Exception raised when the deletion of a shortened URL fails.

    Attributes:
        message (str): Explanation of the error.
    """

    def __init__(self, message="Failed to delete the shortened URL."):
        self.message = message
        super().__init__(self.message)
