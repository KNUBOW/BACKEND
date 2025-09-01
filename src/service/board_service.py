import uuid
import boto3
from fastapi import Request, UploadFile
from botocore.exceptions import BotoCoreError, NoCredentialsError

from core.config import settings
from exception.board_exception import BoardNotFoundException, AwsError, CommentNotFoundException
from exception.user_exception import HaveNotPermissionException

class BoardService:
    def __init__(self, user_repo, board_repo, user_service, access_token: str, req: Request,):
        self.user_repo = user_repo
        self.board_repo = board_repo
        self.user_service = user_service
        self.access_token = access_token
        self.req = req
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY.get_secret_value(),
            region_name="ap-northeast-2"
        )

    async def get_current_user(self):
        return await self.user_service.get_user_by_token(self.access_token, self.req)

    async def upload_to_s3(self, file: UploadFile) -> str:
        try:
            file_key = f"board/{uuid.uuid4()}_{file.filename}"
            self.s3_client.upload_fileobj(
                file.file,
                settings.AWS_BUCKET_NAME,
                file_key,
            )
            return f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        except (BotoCoreError, NoCredentialsError) as e:
            raise AwsError(detail=str(e))

    async def create_board(self, title: str, content: str, images: list[UploadFile]):
        current_user = await self.get_current_user()

        image_urls = []
        if images:
            for img in images:
                url = await self.upload_to_s3(img)
                image_urls.append(url)

        has_images = len(image_urls) > 0

        board = await self.board_repo.create_board_with_images(
            user_id=current_user.id,
            title=title,
            content=content,
            image_urls=image_urls,
            exist_image=has_images
        )

        return {
            "board_id": board.id
        }

    async def get_board(self, board_id: int):
        board = await self.board_repo.get_board(board_id)
        if not board:
            raise BoardNotFoundException
        return board

    async def get_all_boards(self, skip: int, limit: int, title: str | None = None, nickname: str | None = None):
        board_data = await self.board_repo.get_all_boards(skip=skip, limit=limit, title=title, nickname=nickname)

        result_boards = []
        for board, nickname in board_data:
            result_boards.append({
                "id": board.id,
                "title": board.title,
                "nickname": nickname,
                "like_count": board.like_count,
                "exist_image": board.exist_image,
                "created_at": board.created_at,
            })

        return result_boards

    async def soft_delete_board(self, board_id: int):
        current_user = await self.get_current_user()

        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundException

        if board.user_id != current_user.id:
            raise HaveNotPermissionException(detail="삭제권한이 없습니다.")

        await self.board_repo.soft_delete_board(board_id)
        return {"message": "게시글이 성공적으로 삭제되었습니다."}

    async def like_board(self, board_id: int):
        current_user = await self.get_current_user()

        like = await self.board_repo.toggle_like(current_user.id, board_id)

        if like:
            return {"message": "게시글을 추천했습니다."}
        else:
            return {"message": "게시글 추천을 취소했습니다."}

    async def create_comment(self, board_id: int, comment: str):
        current_user = await self.get_current_user()

        board = await self.board_repo.get_board(board_id)
        if not board:
            raise BoardNotFoundException

        return await self.board_repo.create_comment(
            user_id=current_user.id,
            board_id=board_id,
            comment=comment
        )

    async def get_comments(self, board_id: int):
        board = await self.board_repo.get_board(board_id)
        if not board:
            raise BoardNotFoundException

        comments = await self.board_repo.get_comments_by_board_id(board_id)

        result_comments = []
        for comment, nickname in comments:
            result_comments.append({
                "user_nickname": nickname,
                "comment": comment.comment,
                "created_at": comment.created_at
            })

        return result_comments

    async def delete_comment(self, comment_id: int):
        current_user = await self.get_current_user()
        comment = await self.board_repo.get_comment_by_id(comment_id)

        if not comment:
            raise CommentNotFoundException

        if comment.user_id != current_user.id:
            raise HaveNotPermissionException(detail="댓글 삭제 권한이 없습니다.")

        await self.board_repo.soft_delete_comment(comment_id)