import bcrypt
from fastapi import Request
from datetime import datetime, timedelta, date
from jose import jwt, JWTError

from core.config import settings
from database.repository.user_repository import UserRepository
from exception.base_exception import UnexpectedException
from schema.request import SignUpRequest, FindIdRequest, PassWordChangeRequest
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

    def create_jwt(self, email: str) -> str:
        return jwt.encode(
            {
                "sub": email,
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
            email = payload.get("sub")

            if email is None:
                raise TokenExpiredException()

            return email

        except JWTError:
            raise TokenExpiredException()

    async def get_user_by_token(self, access_token: str, req: Request) -> User:
        email: str = self.decode_jwt(access_token)
        user: User | None = await self.user_repo.get_user_by_email(email=email)

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

            user = User.create(
                email=request.email,
                hashed_password=hashed_password,
                name=request.name,
                nickname=request.nickname,
                birth=request.birth,
                gender=request.gender,
                hashed_phone_num=hashed_phone_num
            )

            user = await self.user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except (DuplicateEmailException, DuplicateNicknameException, InvalidCheckedPasswordException) as e:
            raise e # e 넣는 조건은 여러개 일 때 넣음, 단일 조건으로 e를 넣는건 로그 넣으려고 하는거고 단일에선 e안써도 됌

        except Exception as e:  # 그러나 얘는 오류를 출력해야 하기에 e를 씀
            raise UnexpectedException(detail=f"회원가입 중 예기치 못한 오류 발생: {str(e)}")

    async def log_in(self, request: SignUpRequest, req: Request):
        try:
            user = await self.user_repo.get_user_by_email(email=request.email)

            if not user or not self.verify_value(request.password, user.password):
                raise InvalidCredentialsException()

            access_token = self.create_jwt(user.email)

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