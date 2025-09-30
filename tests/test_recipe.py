import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
import httpx

from core.config import settings
from service.recipe_service import FoodThingAIService
from exception.foodthing_exception import (
    AIServiceException,
    AINullResponseException,
    AIJsonDecodeException,
    InvalidAIRequestException
)
from exception.user_exception import TokenExpiredException, UserNotFoundException

# --------------------- Mock 설정 -----------------------
@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.name = "테스트유저"
    user.nickname = "tester"
    return user


@pytest.fixture
def mock_user_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_request():
    return Mock()
# --------------------- Mock 설정 End -----------------------

@pytest.fixture
def ai_service(mock_user_service, mock_user_repo, mock_request):
    with patch('service.recipe_service.settings') as mock_settings:
        mock_settings.OLLAMA_URL = settings.OLLAMA_URL
        mock_settings.OLLAMA_MODEL_NAME = settings.OLLAMA_MODEL_NAME
        mock_settings.OPENAI_API_KEY.get_secret_value.return_value = settings.OPENAI_API_KEY.get_secret_value()

        service = FoodThingAIService(
            user_service=mock_user_service,
            user_repo=mock_user_repo,
            access_token="test_token",
            req=mock_request
        )
        return service


# --------------------- 토큰 설정 -----------------------
class TestGetCurrentUser:

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, ai_service, mock_user_service, mock_user):
        mock_user_service.get_user_by_token.return_value = mock_user

        result = await ai_service.get_current_user()

        assert result == mock_user
        mock_user_service.get_user_by_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_current_user_token_expired(self, ai_service, mock_user_service):
        mock_user_service.get_user_by_token.side_effect = TokenExpiredException()

        with pytest.raises(TokenExpiredException):
            await ai_service.get_current_user()

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, ai_service, mock_user_service):
        mock_user_service.get_user_by_token.return_value = None

        with pytest.raises(UserNotFoundException):
            await ai_service.get_current_user()

# --------------------- 토큰 설정 End -----------------------

# --------------------- Ollama 테스트(로컬 PC 켜져있을 시) -----------------------
class TestCallOllama:

    @pytest.mark.asyncio
    async def test_call_ollama_success(self, ai_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": json.dumps({"food": "계란후라이", "difficulty": 1})
            }
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await ai_service._call_ollama("test prompt")

            assert result["food"] == "계란후라이"
            assert result["_ai_provider"] == "ollama"

    @pytest.mark.asyncio
    async def test_call_ollama_with_json_block(self, ai_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "content": '```json\n{"food": "김치찌개", "difficulty": 3}\n```'
            }
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await ai_service._call_ollama("test prompt")

            assert result["food"] == "김치찌개"

    @pytest.mark.asyncio
    async def test_call_ollama_connection_error_fallback_openai(self, ai_service):
        """Ollama 연결 실패 시 OpenAI로 폴백"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection failed")

            with patch.object(ai_service, '_call_openai', new_callable=AsyncMock) as mock_openai:
                mock_openai.return_value = {"food": "test", "_ai_provider": "openai"}

                result = await ai_service._call_ollama("test prompt")

                assert result["_ai_provider"] == "openai"
                mock_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_ollama_empty_response(self, ai_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": ""}}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AINullResponseException):
                await ai_service._call_ollama("test prompt")

    @pytest.mark.asyncio
    async def test_call_ollama_invalid_json(self, ai_service):
        """잘못된 JSON 응답 처리"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "This is not valid JSON"}
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AIJsonDecodeException):
                await ai_service._call_ollama("test prompt")

# --------------------- Ollama 테스트(로컬 PC 켜져있을 시) END -----------------------

# --------------------- OpenAI 테스트(로컬 PC 꺼져있을 시) -----------------------
class TestCallOpenAI:

    @pytest.mark.asyncio
    async def test_call_openai_success(self, ai_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({"food": "파스타", "difficulty": 3})
                }
            }]
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            result = await ai_service._call_openai("test prompt")

            assert result["food"] == "파스타"
            assert result["_ai_provider"] == "openai"

    @pytest.mark.asyncio
    async def test_call_openai_no_api_key(self, ai_service):
        ai_service.openai_api_key = None

        with pytest.raises(AIServiceException) as exc_info:
            await ai_service._call_openai("test prompt")

        assert "API 키" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_call_openai_network_error(self, ai_service):
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Network error")

            with pytest.raises(AIServiceException) as exc_info:
                await ai_service._call_openai("test prompt")

            assert "네트워크 오류" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_call_openai_http_error(self, ai_service):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

            with pytest.raises(AIServiceException) as exc_info:
                await ai_service._call_openai("test prompt")

            assert "500" in str(exc_info.value.detail)


class TestGetSuggestRecipes:

    @pytest.mark.asyncio
    async def test_get_suggest_recipes_success(self, ai_service, mock_user_service, mock_user_repo, mock_user):
        mock_user_service.get_user_by_token.return_value = mock_user
        mock_user_repo.get_user_ingredients.return_value = ["계란", "양파", "토마토"]

        expected_response = {
            "recipes": [
                {"food": "계란후라이", "use_ingredients": ["계란"], "difficulty": 1}
            ]
        }

        with patch.object(ai_service, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_response

            result = await ai_service.get_suggest_recipes()

            assert "recipes" in result
            mock_user_repo.get_user_ingredients.assert_called_once_with(mock_user.id)

# --------------------- OpenAI 테스트(로컬 PC 꺼져있을 시) -----------------------

class TestGetFoodRecipe:

    @pytest.mark.asyncio
    async def test_get_food_recipe_success(self, ai_service):
        request_data = {
            "food": "김치찌개",
            "use_ingredients": ["김치", "돼지고기", "두부"]
        }

        expected_response = {
            "food": "김치찌개",
            "use_ingredients": [
                {"name": "김치", "amount": "200g"},
                {"name": "돼지고기", "amount": "100g"}
            ],
            "steps": ["1. 김치를 썬다", "2. 고기를 볶는다"],
            "tip": "오래 끓일수록 맛있어요"
        }

        with patch.object(ai_service, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_response

            result = await ai_service.get_food_recipe(request_data)

            assert result["food"] == "김치찌개"
            assert "steps" in result

    @pytest.mark.asyncio
    async def test_get_food_recipe_invalid_request(self, ai_service):
        request_data = {"food": "김치찌개"}

        with pytest.raises(InvalidAIRequestException):
            await ai_service.get_food_recipe(request_data)

    @pytest.mark.asyncio
    async def test_get_food_recipe_empty_food(self, ai_service):
        request_data = {"food": "", "use_ingredients": ["계란"]}

        with pytest.raises(InvalidAIRequestException):
            await ai_service.get_food_recipe(request_data)


class TestGetQuickRecipe:

    @pytest.mark.asyncio
    async def test_get_quick_recipe_success(self, ai_service):
        """빠른 레시피 조회 성공"""
        chat = "계란, 양파, 치즈"

        expected_response = {
            "food": "치즈 오믈렛",
            "use_ingredients": [
                {"name": "계란", "amount": "2개"},
                {"name": "치즈", "amount": "30g"}
            ],
            "steps": ["1. 계란을 푼다", "2. 팬에 볶는다"],
            "tip": "약불로 천천히"
        }

        with patch.object(ai_service, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_response

            result = await ai_service.get_quick_recipe(chat)

            assert result["food"] == "치즈 오믈렛"


class TestGetSearchRecipe:

    @pytest.mark.asyncio
    async def test_get_search_recipe_success(self, ai_service):
        chat = "된장찌개"

        expected_response = {
            "food": "된장찌개",
            "use_ingredients": [
                {"name": "애호박", "amount": "1/4개"},
                {"name": "두부", "amount": "1/2모"}
            ],
            "steps": ["1. 재료 준비", "2. 끓이기"],
            "tip": "멸치 육수 사용"
        }

        with patch.object(ai_service, '_call_ollama', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = expected_response

            result = await ai_service.get_search_recipe(chat)

            assert result["food"] == "된장찌개"
            assert "tip" in result