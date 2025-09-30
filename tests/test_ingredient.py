import pytest
from unittest.mock import MagicMock, AsyncMock

from service.ingredient_service import IngredientService
from schema.request import IngredientRequest
from database.orm import User
from exception.ingredient_exception import IngredientNotFoundException

pytestmark = pytest.mark.asyncio

# --------------------- Mock 설정 -----------------------
@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.fixture
def mock_ingredient_repo():
    repo = MagicMock()

    async def mock_create(ingredient):
        ingredient.id = 1
        return ingredient

    repo.create_ingredient = AsyncMock(side_effect=mock_create)
    repo.get_ingredients = AsyncMock(return_value=[])
    repo.delete_ingredient = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_user_service():
    service = MagicMock()
    service.get_user_by_token = AsyncMock()
    return service


@pytest.fixture
def mock_request():
    return MagicMock()


@pytest.fixture
def mock_user():
    return User(id=1, name="testuser", email="test@example.com")

# --------------------- Mock 설정 End-----------------------

# --------------------- Create, Delete Test -----------------------
class TestIngredientService:

    async def test_create_ingredient(self, mock_user_repo, mock_ingredient_repo, mock_user_service, mock_request,
                                     mock_user):
        mock_user_service.get_user_by_token.return_value = mock_user
        access_token = "fake-token"
        service = IngredientService(mock_user_repo, mock_ingredient_repo, mock_user_service, access_token, mock_request)
        request_data = IngredientRequest(ingredient_name="테스트 당근", category_id=1, purchase_date="2025-09-29")

        await service.create_ingredient(request_data)

        mock_user_service.get_user_by_token.assert_called_once_with(access_token, mock_request)
        mock_ingredient_repo.create_ingredient.assert_called_once()

    async def test_delete_ingredient_not_found_raises_exception(self, mock_user_repo, mock_ingredient_repo,
                                                                mock_user_service, mock_request, mock_user):
        mock_user_service.get_user_by_token.return_value = mock_user
        mock_ingredient_repo.delete_ingredient.return_value = False
        access_token = "fake-token"
        service = IngredientService(mock_user_repo, mock_ingredient_repo, mock_user_service, access_token, mock_request)

        with pytest.raises(IngredientNotFoundException):
            await service.delete_ingredient(ingredient_id=999)

        mock_user_service.get_user_by_token.assert_called_once()
        mock_ingredient_repo.delete_ingredient.assert_called_once_with(mock_user.id, 999)

# --------------------- Create, Delete Test End-----------------------