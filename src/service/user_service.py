import bcrypt
import hashlib
import hmac
from base64 import urlsafe_b64encode

from fastapi import Request
from datetime import datetime, timedelta
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
    PasswordUnchangedException, PasswordMismatchException, PasswordLengthException, DuplicatePhoneNumException


class UserService:

    encoding = "UTF-8"
    secret_key = settings.JWT_SECRET_KEY.get_secret_value()
    jwt_algorithm = "HS256"

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def hash_password(self, plain_password: str) -> str:
        hashed_password: bytes = bcrypt.hashpw(
            plain_password.encode(self.encoding),
            salt=bcrypt.gensalt(),
        )
        return hashed_password.decode(self.encoding)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode(self.encoding),
            hashed_password.encode(self.encoding)
        )

    def _make_phone_digest(self, phone: str) -> str:
        mac = hmac.new(
            settings.PHONE_PEPPER.get_secret_value().encode("utf-8"),
            phone.encode(self.encoding),
            hashlib.sha256,
        ).digest()
        return urlsafe_b64encode(mac).decode(self.encoding)


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
        email: str = self.decode_jwt(access_token=access_token)
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

            hashed_password = self.hash_password(request.password)
            phone_digest = self._make_phone_digest(request.phone_num)

            if await self.user_repo.get_user_by_phone_num(phone_digest):
                raise DuplicatePhoneNumException()

            user = User(
                email=request.email,
                password=hashed_password,
                name=request.name,
                nickname=request.nickname,
                birth=request.birth,
                gender=request.gender,
                phone_num=phone_digest
            )

            user = await self.user_repo.save_user(user)
            return UserSchema.model_validate(user)

        except (DuplicateEmailException, DuplicateNicknameException, InvalidCheckedPasswordException, DuplicatePhoneNumException) as e:
            raise e

        except Exception as e:
            raise UnexpectedException(detail=f"회원가입 중 예기치 못한 오류 발생: {str(e)}")

    async def log_in(self, request: LogInRequest, req: Request):
        try:
            user = await self.user_repo.get_user_by_email(email=request.email)

            if not user or not self.verify_password(request.password, user.password):
                raise InvalidCredentialsException()

            access_token = self.create_jwt(user.email)

            return JWTResponse(access_token=access_token)


        except InvalidCredentialsException:
            raise

        except Exception as e:
            raise UnexpectedException(detail=f"로그인 중 예기치 못한 오류 발생: {str(e)}")

    async def change_password(self, user: User, request: PassWordChangeRequest):
        if not self.verify_password(request.current_password, user.password):
            raise IncorrectPasswordException()

        if self.verify_password(request.new_password, user.password):
            raise PasswordUnchangedException()

        if request.new_password != request.confirm_password:
            raise PasswordMismatchException()

        if len(request.new_password) < 8 or len(request.new_password) > 20:
            raise PasswordLengthException()

        hashed = self.hash_password(request.new_password)
        await self.user_repo.update_password(user, hashed)

    async def find_id(self, request: FindIdRequest) -> str:
        try:
            candidates = await self.user_repo.find_candidates_for_find_id(
                name=request.name,
                birth=request.birth,
            )
            if not candidates:
                raise UserNotFoundException()

            want = self._make_phone_digest(request.phone_num)
            for u in candidates:
                if u.phone_num and u.phone_num == want:
                    return FindIdResponse(email=mask_email(u.email))

            raise UserNotFoundException()

        except UserNotFoundException:
            raise
        except Exception as e:
            raise UnexpectedException(detail=f"아이디 찾기 중 예기치 못한 오류 발생: {str(e)}")
