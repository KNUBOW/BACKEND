import pytest
from httpx import AsyncClient
from datetime import date

# pytest-asyncio를 사용하므로 모든 테스트 함수에 마킹
pytestmark = pytest.mark.asyncio


class TestUserAuth:

    # 테스트에 사용할 기본 사용자 정보
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "checked_password": "password123",
        "name": "테스트",
        "nickname": "testnickname",
        "birth": date(2000, 1, 1).isoformat(),
        "gender": "male",
        "phone_num": "01012345678"
    }

    # API 엔드포인트 URL
    SIGN_UP_URL = "/users/sign-up"
    LOG_IN_URL = "/users/log-in"

    async def test_user_sign_up_success(self, async_client: AsyncClient):
        request_data = self.user_data

        response = await async_client.post(self.SIGN_UP_URL, json=request_data)

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == self.user_data["email"]
        assert response_data["nickname"] == self.user_data["nickname"]
        assert "id" in response_data

    async def test_user_sign_up_duplicate_email(self, async_client: AsyncClient):
        await async_client.post(self.SIGN_UP_URL, json=self.user_data)

        duplicate_request_data = self.user_data.copy()
        duplicate_request_data["nickname"] = "다른닉네임"
        duplicate_request_data["phone_num"] = "01087654321"

        response = await async_client.post(self.SIGN_UP_URL, json=duplicate_request_data)

        assert response.status_code == 409
        assert response.json()["detail"] == "이미 사용 중인 이메일입니다"

    async def test_user_sign_up_password_mismatch(self, async_client: AsyncClient):
        invalid_data = self.user_data.copy()
        invalid_data["checked_password"] = "differentpassword"

        response = await async_client.post(self.SIGN_UP_URL, json=invalid_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "비밀번호와 비밀번호 확인이 일치하지 않습니다"

    async def test_user_log_in_success(self, async_client: AsyncClient):
        await async_client.post(self.SIGN_UP_URL, json=self.user_data)

        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }

        response = await async_client.post(self.LOG_IN_URL, json=login_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert isinstance(response_data["access_token"], str)

    async def test_user_log_in_wrong_password(self, async_client: AsyncClient):
        await async_client.post(self.SIGN_UP_URL, json=self.user_data)

        login_data = {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        }

        response = await async_client.post(self.LOG_IN_URL, json=login_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "이메일 또는 비밀번호가 잘못되었습니다"

    async def test_user_log_in_not_registered_email(self, async_client: AsyncClient):
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword"
        }

        response = await async_client.post(self.LOG_IN_URL, json=login_data)

        assert response.status_code == 401
        assert response.json()["detail"] == "이메일 또는 비밀번호가 잘못되었습니다"