class RecommendationRepositoryError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class SpotInfoRepositoryError(Exception):
    def __init__(self, message: str):
        super().__init__(message)