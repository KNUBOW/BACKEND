class CustomException(Exception):

    def __init__(self, status_code: int = 400, detail: str = "에러 발생", code: str = "ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.code = code

class UnexpectedException(CustomException):

    def __init__(self, detail="예기치 못한 오류"):
        super().__init__(status_code=500, code="UNEXPECTED_ERROR", detail=detail)
