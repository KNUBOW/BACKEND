import bcrypt
from fastapi import Request
from datetime import datetime, timedelta, date
from jose import jwt, JWTError

from core.config import settings
from database.repository.user_repository import UserRepository
from exception.base_exception import UnexpectedException
from schema.request import SignUpRequest, FindIdRequest, PassWordChangeRequest, LogInRequest
from database.orm import User
from schema.response import UserSchema, JWTResponse, FindIdResponse
from util.mask_email import mask_email

from exception.user_exception import DuplicateEmailException, DuplicateNicknameException, TokenExpiredException, \
    InvalidCheckedPasswordException, InvalidCredentialsException, UserNotFoundException, IncorrectPasswordException, \
    PasswordUnchangedException, PasswordMismatchException, PasswordLengthException

class UserService:

    encoding = "UTF-8"
    secret_key = settings.JWT_SECRET_KEY.get_secret_value()
    jwt_algorithm = "HS256"

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def hash_value(self, plain_value: str) -> str:
        hashed: bytes = bcrypt.hashpw(
            plain_value.encode(self.encoding),
            salt=bcrypt.gensalt(),
        )
        return hashed.decode(self.encoding)

    def verify_value(self, plain_value: str, hashed_value: str) -> bool:
        return bcrypt.checkpw(
            plain_value.encode(self.encoding),
            hashed_value.encode(self.encoding),
        )

    def create_jwt(self, user_id: int) -> str:
        return jwt.encode(
            {
                "sub": user_id,
                "exp": datetime.now() + timedelta(days=1),
            },
            self.secret_key,
            algorithm=self.jwt_algorithm,
        )

    def decode_jwt(self, access_token: str) -> str:
        try:
            payload: dict = jwt.decode(
                access_token, self.secret_key, algorithms=[self.jwt_algorithm]
            )
            user_id = payload.get("sub")

            if user_id is None:
                raise TokenExpiredException()

            return user_id

        except JWTError:
            raise TokenExpiredException()

    async def get_user_by_token(self, access_token: str, req: Request) -> User:
        user_id: int = self.decode_jwt(access_token)
        user: User | None = await self.user_repo.get_user_by_id(user_id=user_id)

        if not user:
            raise UserNotFoundException()
        return user

    async def sign_up(self, request: SignUpRequest):

        try:
            if await self.user_repo.get_user_by_email(request.email):
                raise DuplicateEmailException()

            if await self.user_repo.get_user_by_nickname(request.nickname):
                raise DuplicateNicknameException()

            if request.password != request.checked_password:
                raise InvalidCheckedPasswordException()

            hashed_password = self.hash_value(request.password)
            hashed_phone_num = self.hash_value(request.phone_num)

            user = User(
                email=request.email,
                password=hashed_password,
                name=request.name,
                nickname=request.nickname,
                birth=request.birth,
                gender=request.gender,
                phone_num=hashed_phone_num
            )

            user = await self.user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except (DuplicateEmailException, DuplicateNicknameException, InvalidCheckedPasswordException) as e:
            raise e

        except Exception as e:
            raise UnexpectedException(detail=f"회원가입 중 예기치 못한 오류 발생: {str(e)}")

    async def log_in(self, request: LogInRequest, req: Request):
        try:
            user = await self.user_repo.get_user_by_email(email=request.email)

            if not user or not self.verify_value(request.password, user.password):
                raise InvalidCredentialsException()

            access_token = self.create_jwt(user.id)

            return JWTResponse(access_token=access_token)


        except InvalidCredentialsException:
            raise

        except Exception as e:
            raise UnexpectedException(detail=f"로그인 중 예기치 못한 오류 발생: {str(e)}")

    async def change_password(self, user: User, request: PassWordChangeRequest):
        if not self.verify_value(request.current_password, user.password):
            raise IncorrectPasswordException()

        if self.verify_value(request.new_password, user.password):
            raise PasswordUnchangedException()

        if request.new_password != request.confirm_password:
            raise PasswordMismatchException()

        if len(request.new_password) < 8 or len(request.new_password) > 20:
            raise PasswordLengthException()

        hashed = self.hash_value(request.new_password)
        await self.user_repo.update_password(user, hashed)


    async def find_id(self, request: FindIdRequest) -> str:
        try:
            user = await self.user_repo.get_user_by_name(request.name)

            if not user or user.birth != request.birth:
                raise UserNotFoundException()

            if not user or not self.verify_value(request.phone_num, user.phone_num):
                raise UserNotFoundException()

            masked_email = mask_email(user.email)
            return FindIdResponse(email=masked_email)

        except UserNotFoundException:
            raise

        except Exception as e:
            raise UnexpectedException(detail=f"아이디 찾기 중 예기치 못한 오류 발생: {str(e)}")