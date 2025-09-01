from .base_exception import CustomException


class BoardNotFoundException(CustomException):
    def __init__(self, detail="게시글을 찾을 수 없습니다."):
        super().__init__(status_code=404, detail=detail, code="BOARD_NOT_FOUND")

class AwsError(CustomException):
    def __init__(self, detail="AWS 이슈"):
        super().__init__(status_code=500, detail=detail, code="AWS_ISSUE")

class CommentNotFoundException(CustomException):
    def __init__(self, detail="댓글을 찾을 수 없습니다."):
        super().__init__(status_code=404, detail=detail, code="COMMENT_NOT_FOUND")