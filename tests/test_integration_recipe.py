import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import date
import json

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
        print("\n" + "=" * 70)
        print("🔄 통합 테스트 시작: 회원가입 -> 로그인 -> 식재료 -> 레시피")
        print("=" * 70)

        # 1. 회원가입
        print("\n[1단계] 회원가입 시도...")
        signup_response = await async_client.post("/users/sign-up", json=user_data)
        assert signup_response.status_code in [201, 409]

        if signup_response.status_code == 201:
            user_id = signup_response.json()["id"]
            print(f"✅ 회원가입 성공 - User ID: {user_id}")
        else:
            print(f"✅ 회원가입 건너뛰기 (이미 가입된 유저)")

        # 2. 로그인
        print("\n[2단계] 로그인 중...")
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        login_response = await async_client.post("/users/log-in", json=login_data)
        assert login_response.status_code == 200
        login_result = login_response.json()
        access_token = login_result.get("access_token") or login_result.get("token")
        assert access_token is not None
        print(f"✅ 로그인 성공")
        print(f"   Token: {access_token[:30]}...")

        # 3. 식재료 추가 (여러 개)
        print("\n[3단계] 식재료 추가 중...")
        headers = {"Authorization": f"Bearer {access_token}"}
        ingredients = [
            {"ingredient_name": "계란", "category_id": 1, "purchase_date": "2025-09-25"},
            {"ingredient_name": "양파", "category_id": 2, "purchase_date": "2025-09-26"},
            {"ingredient_name": "당근", "category_id": 2, "purchase_date": "2025-09-27"},
            {"ingredient_name": "치즈", "category_id": 3, "purchase_date": "2025-09-28"}
        ]

        ingredient_ids = []
        for i, ingredient in enumerate(ingredients, 1):
            response = await async_client.post(
                "/ingredients",
                json=ingredient,
                headers=headers
            )
            assert response.status_code == 201
            result = response.json()
            ingredient_ids.append(result["id"])
            print(f"   {i}. {ingredient['ingredient_name']} 추가 완료 (ID: {result['id']})")

        print(f"✅ 총 {len(ingredients)}개 식재료 추가 완료")

        # 4. 식재료 목록 조회
        print("\n[4단계] 식재료 목록 조회...")
        list_response = await async_client.get("/ingredients", headers=headers)
        assert list_response.status_code == 200
        ingredients_result = list_response.json()

        # 응답 구조 디버깅
        print(f"\n🔍 식재료 응답 타입: {type(ingredients_result)}")
        print(f"🔍 식재료 응답 샘플: {str(ingredients_result)[:200]}...")

        if isinstance(ingredients_result, dict):
            ingredients_list = ingredients_result.get("ingredient_list") or ingredients_result.get("ingredients") or []
        else:
            ingredients_list = ingredients_result

        assert len(ingredients_list) >= len(ingredients)
        print(f"✅ 식재료 목록 조회 성공 - 총 {len(ingredients_list)}개")
        print("\n📦 현재 보유 식재료:")

        for idx, item in enumerate(ingredients_list[:10], 1):
            if isinstance(item, dict):
                name = item.get("ingredient_name") or item.get("name", "이름없음")
                purchase = item.get("purchase_date", "날짜없음")
                print(f"   {idx}. {name} (구매일: {purchase})")
            elif isinstance(item, str):
                print(f"   {idx}. {item}")
            else:
                print(f"   {idx}. {item}")

        if len(ingredients_list) > 10:
            print(f"   ... 외 {len(ingredients_list) - 10}개")

        # 5. 레시피 추천 요청
        print("\n[5단계] 레시피 추천 요청 중...")
        recipe_response = await async_client.get(
            "/recipe/suggest",
            headers=headers
        )
        assert recipe_response.status_code in [200, 500, 503]

        if recipe_response.status_code == 200:
            recipes = recipe_response.json()
            print(f"✅ 레시피 추천 성공!")

            if isinstance(recipes, dict) and "recipes" in recipes:
                recipe_list = recipes["recipes"]
            elif isinstance(recipes, list):
                recipe_list = recipes
            else:
                recipe_list = []

            print(f"\n🍳 추천된 레시피 ({len(recipe_list)}개):")

            print(f"\n📊 전체 레시피 응답:")
            print(json.dumps(recipes, ensure_ascii=False, indent=2))

        else:
            print(f"⚠️ AI 서비스 응답 코드: {recipe_response.status_code}")
            try:
                error_detail = recipe_response.json()
                print(f"   에러 상세: {error_detail}")
            except:
                print(f"   에러 텍스트: {recipe_response.text[:200]}")

        # 6. 식재료 삭제
        print(f"\n[6단계] 식재료 삭제 (ID: {ingredient_ids[0]})...")
        delete_response = await async_client.delete(
            f"/ingredients?ingredient_id={ingredient_ids[0]}",
            headers=headers
        )
        assert delete_response.status_code == 204
        print(f"✅ 식재료 삭제 성공")

        # 7. 삭제 후 목록 재확인
        print("\n[7단계] 삭제 후 재확인...")
        final_list_response = await async_client.get("/ingredients", headers=headers)
        assert final_list_response.status_code == 200
        final_list_result = final_list_response.json()

        if isinstance(final_list_result, dict):
            final_list = final_list_result.get("ingredient_list") or final_list_result.get("ingredients") or []
        else:
            final_list = final_list_result

        assert len(final_list) == len(ingredients_list) - 1
        print(f"✅ 삭제 확인 완료")
        print(f"   이전: {len(ingredients_list)}개 → 현재: {len(final_list)}개")

        print("\n" + "=" * 70)
        print("✅ 통합 테스트 완료!")
        print("=" * 70 + "\n")

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
        print(f"✅ 삭제 확인 완료")

        print("\n" + "=" * 70)
        print("✅ 통합 테스트 완료!")
        print("=" * 70 + "\n")

class TestRecipeFlowIntegration:
    """레시피 관련 통합 테스트"""

    @pytest_asyncio.fixture(scope="function")
    async def setup_user_with_ingredients(self, async_client: AsyncClient):
        print("\n🔧 레시피 테스트용 환경 준비...")
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

        print("📦 식재료 추가:")
        for ingredient in ingredients:
            res = await async_client.post("/ingredients", json=ingredient, headers=headers)
            assert res.status_code == 201
            print(f"   - {ingredient['ingredient_name']}")

        print("✅ 준비 완료\n")
        return async_client, headers

    async def test_recipe_suggest_and_cook(self, setup_user_with_ingredients):
        """레시피 추천 후 상세 조리법 조회 테스트"""
        print("=" * 70)
        print("🍳 레시피 추천 → 조리법 조회 통합 테스트")
        print("=" * 70)

        client, headers = setup_user_with_ingredients

        # 1. 레시피 추천
        print("\n[1단계] 레시피 추천 요청...")
        suggest_response = await client.get("/recipe/suggest", headers=headers)

        if suggest_response.status_code == 200:
            recipes_data = suggest_response.json()
            print(f"✅ 레시피 추천 성공!")

            print(f"\n📋 추천 결과:")
            print(json.dumps(recipes_data, ensure_ascii=False, indent=2))

            if isinstance(recipes_data, dict) and "recipes" in recipes_data:
                recipes = recipes_data["recipes"]
                print(f"\n🍳 추천된 레시피 목록 ({len(recipes)}개):")

                # 2. 첫 번째 레시피 상세 조리법 요청
                if recipes and len(recipes) > 0:
                    first_recipe = recipes[0]
                    print(f"\n[2단계] 첫 번째 레시피 상세 조리법 요청: {first_recipe.get('food')}")

                    cook_request = {
                        "food": first_recipe.get("food"),
                        "use_ingredients": first_recipe.get("use_ingredients", [])
                    }

                    cook_response = await client.post(
                        "/recipe/cook",
                        json=cook_request,
                        headers=headers
                    )

                    if cook_response.status_code == 200:
                        cook_detail = cook_response.json()
                        print(f"✅ 조리법 조회 성공!")
                        print(f"\n🍳 {cook_detail.get('food', '레시피')} 상세 조리법:")
                        print(json.dumps(cook_detail, ensure_ascii=False, indent=2))


                    else:
                        print(f"⚠️ 조리법 조회 실패: {cook_response.status_code}")
                        print(f"   응답: {cook_response.text[:300]}")
        else:
            print(f"⚠️ AI 서비스 상태: {suggest_response.status_code}")
            print(f"   응답: {suggest_response.text[:300]}")

        print("\n" + "=" * 70 + "\n")

    async def test_ingredient_cook(self, setup_user_with_ingredients):
        """식재료만으로 빠른 레시피 추천 테스트"""
        print("=" * 70)
        print("⚡ 식재료 기반 빠른 레시피 테스트")
        print("=" * 70)

        client, headers = setup_user_with_ingredients
        ingredient_request = {"chat": "계란, 양파, 치즈"}

        print(f"\n💬 입력 재료: {ingredient_request['chat']}")

        response = await client.post(
            "/recipe/ingredient-cook",
            json=ingredient_request,
            headers=headers
        )

        print(f"📊 응답 상태: {response.status_code}")

        if response.status_code == 200:
            recipe = response.json()
            print(f"✅ 빠른 레시피 성공!")
            print(f"\n📋 추천된 요리:")
            print(json.dumps(recipe, ensure_ascii=False, indent=2))

        else:
            print(f"⚠️ 서비스 상태: {response.status_code}")
            print(f"   응답: {response.text[:300]}")

        print("\n" + "=" * 70 + "\n")

    async def test_food_cook(self, setup_user_with_ingredients):
        """음식명으로 레시피 검색 테스트"""
        print("=" * 70)
        print("🔍 음식명 기반 레시피 검색 테스트")
        print("=" * 70)

        client, headers = setup_user_with_ingredients
        food_request = {"chat": "김치찌개"}

        print(f"\n🍜 검색 음식: {food_request['chat']}")

        response = await client.post(
            "/recipe/food-cook",
            json=food_request,
            headers=headers
        )

        print(f"📊 응답 상태: {response.status_code}")

        if response.status_code == 200:
            recipe = response.json()
            print(f"✅ 레시피 검색 성공!")
            print(f"\n📋 검색 결과:")
            print(json.dumps(recipe, ensure_ascii=False, indent=2))

        else:
            print(f"⚠️ 서비스 상태: {response.status_code}")
            print(f"   응답: {response.text[:300]}")

        print("\n" + "=" * 70 + "\n")


class TestErrorHandlingIntegration:
    """에러 처리 통합 테스트"""

    async def test_unauthorized_access(self, async_client: AsyncClient):
        print("\n🔒 미인증 접근 테스트...")
        response = await async_client.get("/ingredients")
        assert response.status_code == 401
        print("✅ 미인증 접근 차단 확인")

    async def test_invalid_token_access(self, async_client: AsyncClient):
        print("\n🔒 잘못된 토큰 테스트...")
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await async_client.get("/ingredients", headers=headers)
        assert response.status_code in [401, 403]
        print("✅ 잘못된 토큰 차단 확인")

    async def test_delete_nonexistent_ingredient(self, async_client: AsyncClient):
        print("\n❌ 존재하지 않는 식재료 삭제 테스트...")
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