from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, delete
from sqlalchemy.orm import selectinload

from database.orm import Board, BoardImage, User, BoardLike, BoardComment
from database.repository.base_repository import commit_with_error_handling
from exception.board_exception import BoardNotFoundException


class BoardRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_board_with_images(self, user_id: int, title: str, content: str, image_urls: list[str], exist_image: bool) -> Board:
        board = Board(user_id=user_id, title=title, content=content, exist_image=exist_image)
        self.session.add(board)

        board_images = []
        for url in image_urls:
            board_image = BoardImage(image_url=url, board=board)
            board_images.append(board_image)
        self.session.add_all(board_images)

        await commit_with_error_handling(self.session)
        await self.session.refresh(board)
        return board

    async def get_board(self, board_id: int) -> Board | None:
        query = (
            select(Board)
            .options(
                selectinload(Board.user),
                selectinload(Board.images)
            )
            .where(Board.id == board_id, Board.status == True)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_boards(self, skip: int, limit: int, title: str | None = None, nickname: str | None = None) -> \
    list[Board]:
        stmt = select(Board).options(selectinload(Board.user))

        if nickname:
            stmt = stmt.join(User, Board.user_id == User.id)

        stmt = stmt.where(Board.status == True)

        if title:
            stmt = stmt.where(Board.title.like(f"%{title}%"))
        if nickname:
            stmt = stmt.where(User.nickname.like(f"%{nickname}%"))

        stmt = stmt.order_by(desc(Board.created_at)).offset(skip).limit(limit)

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def soft_delete_board(self, board_id: int):
        board = await self.get_board(board_id)
        if board:
            board.status = False
            await commit_with_error_handling(self.session)

    async def toggle_like(self, user_id: int, board_id: int):
        stmt = select(BoardLike).where(
            BoardLike.user_id == user_id,
            BoardLike.board_id == board_id
        )
        existing_like = await self.session.execute(stmt)
        existing_like = existing_like.scalar_one_or_none()

        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundException

        if existing_like:
            await self.session.execute(
                delete(BoardLike).where(
                    BoardLike.user_id == user_id,
                    BoardLike.board_id == board_id
                )
            )
            board.like_count -= 1

            await commit_with_error_handling(self.session)
            return False

        else:
            new_like = BoardLike(user_id=user_id, board_id=board_id)
            self.session.add(new_like)
            board.like_count += 1

            await commit_with_error_handling(self.session)
            return True

    async def create_comment(self, user_id: int, board_id: int, comment: str):
        new_comment = BoardComment(
            user_id=user_id,
            board_id=board_id,
            comment=comment
        )
        self.session.add(new_comment)
        await commit_with_error_handling(self.session)
        await self.session.refresh(new_comment)
        return new_comment

    async def get_comments_by_board_id(self, board_id: int):
        stmt = select(BoardComment, User.nickname).join(
            User, BoardComment.user_id == User.id
        ).where(
            BoardComment.board_id == board_id,
            BoardComment.status == True
        ).order_by(desc(BoardComment.created_at))

        result = await self.session.execute(stmt)
        return result.all()

    async def get_comment_by_id(self, comment_id: int):
        result = await self.session.execute(
            select(BoardComment).where(BoardComment.id == comment_id, BoardComment.status == True)
        )
        return result.scalar_one_or_none()

    async def soft_delete_comment(self, comment_id: int):
        comment = await self.get_comment_by_id(comment_id)
        if comment:
            comment.status = False
            await commit_with_error_handling(self.session)