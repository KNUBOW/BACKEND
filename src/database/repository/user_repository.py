from sqlalchemy import select
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import Optional, Any


from database.orm import User
from exception.database_exception import DatabaseException
from util.base_exception import UnexpectedException
from util.base_repository import commit_with_error_handling


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_by_field(self, field_name: str, value: Any) -> Optional[User]:
        try:
            field = getattr(User, field_name)
            stmt: Select = select(User).where(field == value)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(detail=f"DB 조회 오류: {str(e)}")
        except Exception as e:
            raise UnexpectedException(detail=f"예기치 못한 에러: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self._get_user_by_field("email", email)

    async def get_user_by_nickname(self, nickname: str) -> Optional[User]:
        return await self._get_user_by_field("nickname", nickname)

    async def save_user(self, user: User) -> User:
        self.session.add(user)
        await commit_with_error_handling(self.session, context="유저 저장")
        await self.session.refresh(user)
        return user

    async def update_password(self, user: User, hashed_password: str) -> None:
        user.password = hashed_password
        self.session.add(user)
        await commit_with_error_handling(self.session, context="비밀번호 변경")