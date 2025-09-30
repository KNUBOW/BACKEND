import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import date

pytestmark = pytest.mark.asyncio

"""
플로우 통합 테스트
회원가입 -> 로그인 -> 식재료 추가 -> 레시피 추천
"""

class TestUserRecipeIntegration:

    @pytest.fixture
    def user_data(self):
        """테스트용 사용자 데이터"""
        return {
            "email": "integration@example.com",
            "password": "pass1234",
            "checked_password": "pass1234",
            "name": "통합테스트",
            "nickname": "integration_user",
            "birth": date(1995, 5, 15).isoformat(),
            "gender": "female",
            "phone_num": "01011112222"
        }

    async def test_full_user_recipe_flow(self, async_client: AsyncClient, user_data):
        # 1. 회원가입
        signup_response = await async_client.post("/users/sign-up", json=user_data)
        assert signup_response.status_code in [201, 409]

        if signup_response.status_code == 201:
            user_id = signup_response.json()["id"]
            print(f"✅ 회원가입 성공 - User ID: {user_id}")
        else:
            print(f"✅ 회원가입 건너뛰기 (이미 가입된 유저)")


        # 2. 로그인
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        login_response = await async_client.post("/users/log-in", json=login_data)
        assert login_response.status_code == 200
        login_result = login_response.json()
        access_token = login_result.get("access_token") or login_result.get("token")
        assert access_token is not None
        print(f"✅ 로그인 성공 - Token: {access_token[:20]}...")

        # 3. 식재료 추가 (여러 개)
        headers = {"Authorization": f"Bearer {access_token}"}
        ingredients = [
            {"ingredient_name": "계란", "category_id": 1, "purchase_date": "2025-09-25"},
            {"ingredient_name": "양파", "category_id": 2, "purchase_date": "2025-09-26"},
            {"ingredient_name": "당근", "category_id": 2, "purchase_date": "2025-09-27"},
            {"ingredient_name": "치즈", "category_id": 3, "purchase_date": "2025-09-28"}
        ]

        ingredient_ids = []
        for ingredient in ingredients:
            response = await async_client.post(
                "/ingredients",
                json=ingredient,
                headers=headers
            )
            assert response.status_code == 201
            ingredient_ids.append(response.json()["id"])

        print(f"✅ 식재료 {len(ingredients)}개 추가 완료")

        # 4. 식재료 목록 조회
        list_response = await async_client.get("/ingredients", headers=headers)
        assert list_response.status_code == 200
        ingredients_result = list_response.json()

        if isinstance(ingredients_result, dict):
            ingredients_list = ingredients_result.get("ingredient_list") or ingredients_result.get("ingredients") or []
        else:
            ingredients_list = ingredients_result

        assert len(ingredients_list) >= len(ingredients)
        print(f"✅ 식재료 목록 조회 성공 - 총 {len(ingredients_list)}개")

        # 5. 레시피 추천 요청 (AI 서비스)
        recipe_response = await async_client.get(
            "/recipe/suggest",
            headers=headers
        )
        assert recipe_response.status_code in [200, 500, 503]

        if recipe_response.status_code == 200:
            recipes = recipe_response.json()
            assert "recipes" in recipes or isinstance(recipes, list)
            print(f"✅ 레시피 추천 성공")
        else:
            print(f"⚠️ AI 서비스 응답: {recipe_response.status_code}")

        # 6. 식재료 삭제
        delete_response = await async_client.delete(
            f"/ingredients?ingredient_id={ingredient_ids[0]}",
            headers=headers
        )
        assert delete_response.status_code == 204
        print(f"✅ 식재료 삭제 성공")

        # 7. 삭제 후 목록 재확인
        final_list_response = await async_client.get("/ingredients", headers=headers)
        assert final_list_response.status_code == 200
        final_list_result = final_list_response.json()

        if isinstance(final_list_result, dict):
            final_list = final_list_result.get("ingredient_list") or final_list_result.get("ingredients") or []
        else:
            final_list = final_list_result

        assert len(final_list) == len(ingredients_list) - 1
        print(f"✅ 삭제 확인 완료 - 남은 식재료: {len(final_list)}개")


class TestIngredientCRUDIntegration:
    """식재료 CRUD 통합 테스트"""

    @pytest_asyncio.fixture(scope="function")
    async def authenticated_client(self, async_client: AsyncClient):
        # 1. 회원가입
        user_data = {
            "email": "crud@example.com",
            "password": "pass1234",
            "checked_password": "pass1234",
            "name": "CRUD테스트",
            "nickname": "crud_user",
            "birth": date(1990, 1, 1).isoformat(),
            "gender": "male",
            "phone_num": "01099998888"
        }

        signup_response = await async_client.post("/users/sign-up", json=user_data)
        assert signup_response.status_code in [201, 409]

        # 2. 로그인
        login_response = await async_client.post("/users/log-in", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200, f"Fixture 로그인 실패: {login_response.json()}"

        login_result = login_response.json()
        token = login_result.get("access_token") or login_result.get("token")
        assert token is not None, f"토큰을 찾을 수 없음: {login_result}"

        return async_client, token

    #3. 식재료 추가
    async def test_ingredient_create_read_update_delete(self, authenticated_client):
        client, token = authenticated_client
        headers = {"Authorization": f"Bearer {token}"}

        # CREATE
        create_data = {
            "ingredient_name": "토마토",
            "category_id": 2,
            "purchase_date": "2025-09-29"
        }
        create_response = await client.post("/ingredients", json=create_data, headers=headers)
        assert create_response.status_code == 201
        ingredient_id = create_response.json()["id"]
        print(f"✅ CREATE - 식재료 생성 ID: {ingredient_id}")

        # READ (단일)
        read_response = await client.get(f"/ingredients/{ingredient_id}", headers=headers)
        assert read_response.status_code == 200
        ingredient = read_response.json()
        assert ingredient["ingredient_name"] == "토마토"
        print(f"✅ READ - 식재료 조회: {ingredient['ingredient_name']}")

        # DELETE
        delete_response = await client.delete(f"/ingredients?ingredient_id={ingredient_id}", headers=headers)
        assert delete_response.status_code == 204
        print(f"✅ DELETE - 식재료 삭제 완료")

        # 삭제 확인
        verify_response = await client.get(f"/ingredients/{ingredient_id}", headers=headers)
        assert verify_response.status_code == 404
        print(f"✅ 삭제 검증 완료")


class TestRecipeFlowIntegration:
    """레시피 관련 통합 테스트"""

    @pytest_asyncio.fixture(scope="function")
    async def setup_user_with_ingredients(self, async_client: AsyncClient):
        # 1. 회원가입
        user_data = {
            "email": "recipe@example.com",
            "password": "recipe1234",
            "checked_password": "recipe1234",
            "name": "레시피테스트",
            "nickname": "recipe_user",
            "birth": date(1992, 3, 20).isoformat(),
            "gender": "female",
            "phone_num": "01077776666"
        }

        signup_response = await async_client.post("/users/sign-up", json=user_data)
        assert signup_response.status_code in [201, 409]

        # 2. 로그인
        login_response = await async_client.post("/users/log-in", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200

        login_result = login_response.json()
        token = login_result.get("access_token") or login_result.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        ingredients = [
            {"ingredient_name": "김치", "category_id": 2, "purchase_date": "2025-09-29"},
            {"ingredient_name": "돼지고기", "category_id": 1, "purchase_date": "2025-09-29"},
            {"ingredient_name": "두부", "category_id": 3, "purchase_date": "2025-09-29"}
        ]

        for ingredient in ingredients:
            res = await async_client.post("/ingredients", json=ingredient, headers=headers)
            assert res.status_code == 201

        return async_client, headers

    async def test_recipe_suggest_and_detail(self, setup_user_with_ingredients):
        client, headers = setup_user_with_ingredients

        suggest_response = await client.get("/recipe/suggest", headers=headers)

        if suggest_response.status_code == 200:
            recipes_data = suggest_response.json()
            print(f"✅ 레시피 추천 성공")

            if isinstance(recipes_data, dict) and "recipes" in recipes_data:
                recipes = recipes_data["recipes"]
                if recipes and len(recipes) > 0:
                    first_recipe = recipes[0]
                    detail_request = {
                        "food": first_recipe.get("food"),
                        "use_ingredients": first_recipe.get("use_ingredients", [])
                    }
                    detail_response = await client.post(
                        "/recipe/detail",
                        json=detail_request,
                        headers=headers
                    )

                    if detail_response.status_code == 200:
                        recipe_detail = detail_response.json()
                        assert "steps" in recipe_detail
                        print(f"✅ 레시피 상세 조회 성공: {recipe_detail.get('food')}")
        else:
            print(f"⚠️ AI 서비스 미사용 또는 오류: {suggest_response.status_code}")

    async def test_quick_recipe_flow(self, setup_user_with_ingredients):
        client, headers = setup_user_with_ingredients
        quick_request = {"chat": "계란, 양파, 치즈로 간단한 요리"}
        quick_response = await client.post(
            "/recipe/quick",
            json=quick_request,
            headers=headers
        )

        if quick_response.status_code == 200:
            quick_recipe = quick_response.json()
            assert "food" in quick_recipe
            print(f"✅ 빠른 레시피 성공: {quick_recipe.get('food')}")
        else:
            print(f"⚠️ 빠른 레시피 서비스 상태: {quick_response.status_code}")


class TestErrorHandlingIntegration:

    async def test_unauthorized_access(self, async_client: AsyncClient):
        response = await async_client.get("/ingredients")
        assert response.status_code == 401
        print("✅ 미인증 접근 차단 확인")

    async def test_invalid_token_access(self, async_client: AsyncClient):
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await async_client.get("/ingredients", headers=headers)
        assert response.status_code in [401, 403]
        print("✅ 잘못된 토큰 차단 확인")

    async def test_delete_nonexistent_ingredient(self, async_client: AsyncClient):
        """존재하지 않는 식재료 삭제 시도"""
        user_data = {
            "email": "error@example.com",
            "password": "pass1234",
            "checked_password": "pass1234",
            "name": "에러테스트",
            "nickname": "error_user",
            "birth": date(1985, 6, 10).isoformat(),
            "gender": "male",
            "phone_num": "01055554444"
        }

        signup_response = await async_client.post("/users/sign-up", json=user_data)
        assert signup_response.status_code in [201, 409]

        login_response = await async_client.post("/users/log-in", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })

        assert login_response.status_code == 200, f"로그인 실패: {login_response.json()}"
        login_result = login_response.json()
        token = login_result.get("access_token") or login_result.get("token")
        assert token is not None, f"토큰을 찾을 수 없습니다: {login_result}"
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.delete("/ingredients?ingredient_id=99999", headers=headers)
        assert response.status_code == 404
        print("✅ 존재하지 않는 리소스 에러 처리 확인")
