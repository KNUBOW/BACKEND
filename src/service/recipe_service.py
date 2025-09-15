import json
import re
import httpx
from fastapi import Request
from typing import Any, Dict

from core.config import settings
from util.prompt_builder import PromptBuilder
from exception.foodthing_exception import AIServiceException, AINullResponseException, AIJsonDecodeException, \
    InvalidAIRequestException
from exception.user_exception import TokenExpiredException, UserNotFoundException


class FoodThingAIService:
    def __init__(self, user_service, user_repo, access_token: str, req: Request):
        self.ollama_base_url = settings.OLLAMA_URL
        self.model_name = settings.OLLAMA_MODEL_NAME
        self.num_predict = 1000
        self.user_service = user_service
        self.user_repo = user_repo
        self.access_token = access_token
        self.req = req

        self.openai_api_key = settings.OPENAI_API_KEY.get_secret_value()
        self.openai_model_name = "gpt-4o-mini"
        self.openai_base_url = "https://api.openai.com"

    async def get_current_user(self):
        try:
            user = await self.user_service.get_user_by_token(self.access_token, self.req)
        except TokenExpiredException:
            raise
        except Exception as e:
            raise TokenExpiredException(detail=f"토큰 처리 중 오류: {str(e)}")

        if not user:
            raise UserNotFoundException()

        return user

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        if not self.ollama_base_url or not self.model_name:
            return await self._call_openai(prompt)

        timeout = httpx.Timeout(50.0)
        tags_url = f"{self.ollama_base_url.rstrip('/')}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(tags_url)
        except httpx.RequestError:
            return await self._call_openai(prompt)

        chat_url = f"{self.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "num_predict": self.num_predict
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(chat_url, json=payload)
        except httpx.RequestError:
            return await self._call_openai(prompt)

        if response.status_code != 200:
            raise AIServiceException(detail=f"Ollama 호출 실패: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise AIJsonDecodeException(detail=f"Ollama 응답 JSON 디코드 실패: {response.text}")

        message = data.get("message", {})
        response_text = (message.get("content") or "").strip()

        if not response_text:
            response_text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

        if not response_text:
            raise AINullResponseException()

        json_string = response_text
        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            json_string = match.group(1).strip()

        try:
            parsed = json.loads(json_string)
        except json.JSONDecodeError:
            raise AIJsonDecodeException(detail=f"응답 파싱 실패: {response_text}")

        if isinstance(parsed, dict):
            parsed.setdefault("_ai_provider", "ollama")
            return parsed
        else:
            return {"_ai_provider": "ollama", "data": parsed}

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        if not self.openai_api_key:
            raise AIServiceException(detail="OpenAI API 키가 설정되지 않았습니다(OPENAI_API_KEY).")

        timeout = httpx.Timeout(30.0)
        url = f"{self.openai_base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.openai_model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "max_tokens": self.num_predict,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.RequestError as e:
            raise AIServiceException(detail=f"OpenAI 네트워크 오류: {str(e)}")

        if response.status_code != 200:
            raise AIServiceException(detail=f"OpenAI 호출 실패: {response.status_code} - {response.text}")

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise AIJsonDecodeException(detail=f"OpenAI 응답 JSON 디코드 실패: {str(e)}")

        response_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not response_text:
            raise AINullResponseException()

        match = re.search(r"```json\s*([\s\S]+?)\s*```", response_text)
        if match:
            response_text = match.group(1).strip()

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            raise AIJsonDecodeException(detail=f"OpenAI 응답 파싱 실패: {response_text}")

        if isinstance(parsed, dict):
            parsed.setdefault("_ai_provider", "openai")
            return parsed
        else:
            return {"_ai_provider": "openai", "data": parsed}

    async def get_suggest_recipes(self) -> Dict[str, Any]:
        user = await self.get_current_user()
        user_ingredients = await self.user_repo.get_user_ingredients(user.id)

        prompt = PromptBuilder.build_suggestion_prompt(user_ingredients)
        return await self._call_ollama(prompt)

    async def get_food_recipe(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        food = request_data.get("food")
        use_ingredients = request_data.get("use_ingredients", [])

        if not food or not isinstance(use_ingredients, list):
            raise InvalidAIRequestException(detail="올바른 'food' 및 'use_ingredients' 값을 제공해야 합니다.")

        prompt = PromptBuilder.build_recipe_prompt(food, use_ingredients)
        return await self._call_ollama(prompt)

    async def get_quick_recipe(self, chat: str) -> Dict[str, Any]:
        prompt = PromptBuilder.build_quick_prompt(chat)
        return await self._call_ollama(prompt)

    async def get_search_recipe(self, chat: str) -> Dict[str, Any]:
        prompt = PromptBuilder.build_search_prompt(chat)
        return await self._call_ollama(prompt)