import uuid
from fastapi import HTTPException, UploadFile, Request
from database.repository.board_repository import BoardRepository
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from core.config import settings
from database.repository.user_repository import UserRepository
from service.user_service import UserService


class BoardService:
    def __init__(self, board_repo: BoardRepository, user_repo: UserRepository, user_service: UserService, access_token: str, req: Request):
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
            raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")

    async def create_board(self, access_token: str, title: str, content: str, images: list[UploadFile]):
        current_user = self.user_service.get_user_by_access_token(access_token)
        board = await self.board_repo.create_board(current_user, title, content)
        image_urls = []
        if images:
            for img in images:
                url = await self.upload_to_s3(img)
                image_urls.append(url)
            await self.board_repo.add_board_images(board.id, image_urls)

        return {
            "message": "게시글이 등록되었습니다.",
            "board_id": board.id
        }

    async def get_board(self, board_id: int):
        board = await self.board_repo.get_board(board_id)
        if not board:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        return board

    async def get_all_boards(self, skip: int, limit: int):
        return await self.board_repo.get_all_boards(skip, limit)

    async def update_board(self, access_token: str, board_id: int, title: str | None, content: str | None):
        current_user = self.user_service.get_user_by_access_token(access_token)
        board = await self.board_repo.get_board(board_id)
        if not board or board.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

        board = await self.board_repo.update_board(board_id, title, content)
        if not board:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        return {"message": "게시글이 수정되었습니다.", "board_id": board.id}

    async def delete_board(self, access_token: str, board_id: int):
        current_user = self.user_service.get_user_by_access_token(access_token)
        board = await self.board_repo.get_board(board_id)
        if not board or board.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

        image_urls = await self.board_repo.get_board_images(board_id)
        for url in image_urls:
            try:
                key = url.split(f"{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/")[-1]
                self.s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=key)
            except Exception as e:
                print(f"S3 이미지 삭제 실패: {url}, {e}")

        deleted = await self.board_repo.delete_board(board_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="게시글 삭제 중 오류가 발생했습니다.")

        return {"message": "게시글과 이미지가 삭제되었습니다.", "board_id": board_id}