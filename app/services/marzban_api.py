import aiohttp
import json
import time 
from urllib.parse import urljoin 
from config import MARZBAN_API_URL, MARZBAN_USERNAME, MARZBAN_PASSWORD
from typing import Optional, Dict, Any
from datetime import datetime
import sys

class MarzbanAPI:
    def __init__(self):
        self.base_url = MARZBAN_API_URL.rstrip('/')
        self.auth_token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
 
        self.metadata_presets = {
            'free': {'expire': 259200, 'data_limit': 5368709120}, # 5 GB
            '1m': {'expire': 2592000, 'data_limit': 107374182400}, # 100 GB
            '3m': {'expire': 7776000, 'data_limit': 322122547200}, # 300 GB
            '6m': {'expire': 15552000, 'data_limit': 644245094400} # 600 GB
        }

    async def initialize(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self.session = aiohttp.ClientSession(timeout=timeout)

        if not self.auth_token:
            await self._authenticate()
        
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def _get_headers(self, is_json: bool = True) -> Dict[str, str]:
        headers = {"accept": "application/json"}

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if is_json:
             headers["Content-Type"] = "application/json"
        return headers

    async def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None, is_form_data: bool = False) -> Optional[Dict[str, Any]]:
        """Общий асинхронный метод для выполнения HTTP-запросов."""
        
        if self.session is None or self.session.closed:
            try:
                 await self.initialize() 
            except Exception as e:
                 print(f"Ошибка инициализации в _request: {e}")
                 return None

        target_base_url = self.base_url
        
        url = f"{target_base_url.rstrip('/')}/{path.lstrip('/')}"
        
        is_auth_path = path in ["api/admin/token", "admin/token", "token"] 
        headers = self._get_headers(is_json=not is_form_data and not is_auth_path) 
        
        if is_form_data:
            request_kwargs = {'data': data}
        else:
            request_kwargs = {'json': data}
        
        try:
            for attempt in range(3):
                async with self.session.request(
                    method, 
                    url, 
                    headers=headers, 
                    **request_kwargs
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        try:
                            return await response.json()
                        except json.JSONDecodeError:
                            return {} 
                    
                    if method == "GET" and response.status == 404 and "api/user/" in path:
                        return None
                        
                    if response.status >= 500 and attempt < 2:
                        await time.sleep(2 ** attempt) 
                        continue
                        
                    print(f"❌ Marzban API Error ({method} {path}): Status {response.status}. URL: {url}. Response: {response_text}")
                    return None
                    
        except aiohttp.ClientError as e:
            print(f"❌ Marzban Network Error ({method} {path}): {e}")
            return None
        
        return None

    async def _get(self, path: str) -> Optional[Dict[str, Any]]:
        return await self._request("GET", path)

    async def _post(self, path: str, data: Optional[Dict[str, Any]] = None, is_form_data: bool = False) -> Optional[Dict[str, Any]]:
        return await self._request("POST", path, data=data, is_form_data=is_form_data)

    async def _put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        return await self._request("PUT", path, data=data)

    async def _authenticate(self) -> bool:
        """Получает токен аутентификации Marzban, пробуя разные пути."""
        data = {
            "username": MARZBAN_USERNAME,
            "password": MARZBAN_PASSWORD
        }
        
        paths_to_try = ["api/admin/token", "admin/token", "token"]
        
        for path in paths_to_try:
            print(f"Попытка аутентификации, используя путь '{path}'...")
            response = await self._post(path, data=data, is_form_data=True)
            
            if response and "access_token" in response:
                self.auth_token = response["access_token"]
                print(f"Marzban: Аутентификация успешна (использован путь '{path}').")
                return True
        
        print("Marzban: Аутентификация не удалась. Проверьте логин/пароль/URL.")
        return False

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        if not self.auth_token and not await self._authenticate():
             return None
        return await self._get(f"api/user/{username}")

    async def create_user(self, telegram_user_id: int, tariff_code: str, user_data: Dict[str, Any]) -> Optional[str]:
        if not self.auth_token and not await self._authenticate():
            print("Не удалось создать ключ: Ошибка аутентификации.")
            return None

        username = f"tg{telegram_user_id}"
        
        metadata = self.metadata_presets.get(tariff_code)
        if not metadata:
            print(f"Ошибка: метаданные для тарифа {tariff_code} не найдены.")
            return None

        user_info = await self.get_user_info(username)
        
        if user_info:
            print(f"Пользователь '{username}' существует. Обновление (продление) подписки...")
            updated = await self._update_user(username, metadata, user_info)
            if updated:
                if updated.get("subscription_url"):
                    return updated["subscription_url"]
                links = updated.get("links", [])
                for link in links:
                    if link.get("subscription_url"):
                        return link["subscription_url"]
            return None
        else:
            print(f"Пользователь '{username}' не существует. Создание нового ключа (POST)...")
            return await self._create_new_user(username, metadata)

    async def _create_new_user(self, username: str, metadata: Dict[str, int]) -> Optional[str]:
        """Создает нового пользователя и возвращает ссылку."""
        
        expire_duration_s = metadata.get('expire', 0)
        
        future_expire_s = int(time.time()) + expire_duration_s
        
        payload = {
            "username": username,
            "proxies": {
                "vless": {"flow": "xtls-rprx-vision"}
            },
            "status": "active",
            "inbounds": {"vless": ["VLESS TCP REALITY"]}, 
            "data_limit": metadata.get('data_limit'), 
            "data_limit_reset_strategy": "day", 
            "expire": future_expire_s, 
            "note": f"TG ID: {username.lstrip('tg')}",
        }
        
        response = await self._post("api/user", data=payload)
        
        if response and response.get("subscription_url"):
            print(f"Marzban: Пользователь '{username}' успешно создан.")
            return response["subscription_url"]
        return None

    async def _update_user(self, username: str, metadata: Dict[str, int], current_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
  
        expire_duration_s = metadata.get('expire', 0)
        current_expire_raw = current_info.get('expire') or 0
        current_expire_s = int(current_expire_raw)
        current_time_s = int(time.time())
        start_time_s = max(current_expire_s, current_time_s)

        print("--- DEBUG: Расчет продления подписки ---")
        print(f"Текущее время (сек): {current_time_s} ({datetime.fromtimestamp(current_time_s).strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"Текущий expire (сек) от Marzban (НЕОБРАБОТАННЫЙ): {current_expire_raw}")

        expire_date_str = datetime.fromtimestamp(current_expire_s).strftime('%Y-%m-%d %H:%M:%S') if current_expire_s > 0 else 'Нет данных / Истекла'
        print(f"Текущий expire (обработанный, сек): {current_expire_s} ({expire_date_str})")
        print(f"Длительность нового тарифа (сек): {expire_duration_s}")
        print(f"Время отсчета (start_time_s): {start_time_s} ({datetime.fromtimestamp(start_time_s).strftime('%Y-%m-%d %H:%M:%S')})")
        print("---------------------------------------")

        if start_time_s == current_time_s:
             print("Marzban: Подписка истекла или отсутствовала, начинаем отсчет с текущего момента.")
        else:
             print("Marzban: Подписка активна, добавляем время к дате истечения.")
            
        future_expire_s = start_time_s + expire_duration_s

        print(f"Новый expire (сек): {future_expire_s} ({datetime.fromtimestamp(future_expire_s).strftime('%Y-%m-%d %H:%M:%S')})")

        new_data_limit = metadata.get('data_limit', 0) 
        current_data_limit = current_info.get('data_limit', 0) 
        cumulative_data_limit = current_data_limit + new_data_limit
        
        payload = {
            "username": username, 
            "expire": future_expire_s,
            "data_limit": cumulative_data_limit,
            "status": current_info.get("status", "active"), 
            "proxies": current_info.get("proxies", {}), 
            "inbounds": current_info.get("inbounds", {}),
            "data_limit_reset_strategy": current_info.get("data_limit_reset_strategy", "no_reset"),
            "note": current_info.get("note", f"TG ID: {username.lstrip('tg')}"),
        }

        fields_to_remove = ["id", "data_usage", "links", "subscription_url"]
        for field in fields_to_remove:
            if field in current_info:
                del current_info[field]
        
        response = await self._put(f"api/user/{username}", data=payload)
        
        if response:
            print(f"Marzban: Пользователь '{username}' успешно обновлен.")
            return response
        return None
    
    async def disable_user(self, username: str) -> Optional[Dict[str, Any]]:
        current_info = await self.get_user_info(username)
        if not current_info: return None

        payload = {
            "status": "disabled",
            "expire": current_info.get('expire'), 
            "data_limit": current_info.get('data_limit'), 
            "proxies": current_info.get("proxies"), 
            "inbounds": current_info.get("inbounds"),
            "data_limit_reset_strategy": current_info.get("data_limit_reset_strategy"),
            "note": current_info.get("note"),
        }
        payload = {k: v for k, v in payload.items() if v is not None and k not in ["id", "data_usage", "links", "subscription_url"]}

        response = await self._put(f"api/user/{username}", data=payload)
        return response

    async def enable_user(self, username: str) -> Optional[Dict[str, Any]]:
        current_info = await self.get_user_info(username)
        if not current_info: return None

        payload = {
            "status": "active",
            "expire": current_info.get('expire'), 
            "data_limit": current_info.get('data_limit'), 
            "proxies": current_info.get("proxies"), 
            "inbounds": current_info.get("inbounds"),
            "data_limit_reset_strategy": current_info.get("data_limit_reset_strategy"),
            "note": current_info.get("note"),
        }
        payload = {k: v for k, v in payload.items() if v is not None and k not in ["id", "data_usage", "links", "subscription_url"]}
        
        response = await self._put(f"api/user/{username}", data=payload)
        return response

marzban_client = MarzbanAPI()