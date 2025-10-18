import os
from typing import Dict, Any, Optional, Union
import requests


class BitrixService:

    # Метод для создания лида в Bitrix24
    @staticmethod
    def create_lead(lead_fields: Dict[str, Any]) -> Union[int, bool]:
        """
        Создание лида в Bitrix24

        :param lead_fields: поля лида
        :return: результат операции
        """
        # Указываем метод Bitrix24 API для создания лида
        method = "crm.lead.add"
        # Формируем полный URL для API-запроса
        url = f"{os.getenv("WEBHOOK_BITRIX_URL")}/{method}"

        # Формируем тело запроса с полями лида
        payload = {
            "fields": lead_fields
        }

        try:
            from bot.instance import get_app

            app = get_app()
            # Выполняем POST-запрос к Bitrix24 API с таймаутом 30 секунд
            response = requests.post(url, json=payload, timeout=30)
            # Проверяем статус ответа, вызываем исключение при ошибке HTTP
            response.raise_for_status()

            result = response.json()

            # Проверяем наличие ключа 'result' в ответе (успешный запрос)
            if 'result' in result:
                lead_id = result['result']
                if lead_id:
                    # Выводим ID лида для дальнейшего использования
                    app.logger.info(f"Lead successfully created! ID: {lead_id}", "bitrix24")
                    return lead_id
                else:
                    # Выводим сообщение об ошибке создания лида
                    app.logger.error("Failed to create a lead or retrieve its ID", "bitrix24")
                    return False
            else:
                app.logger.error(f"Error while creating a lead: {result}", "bitrix24")
                return False

        except requests.exceptions.Timeout:
            app.logger.error("Timeout while connecting to Bitrix24", "bitrix24")
            return False
        except requests.exceptions.ConnectionError:
            app.logger.error("Connection error while connecting to Bitrix24", "bitrix24")
            return False
        except Exception as e:
            app.logger.error(f"Unexpected error: {e}", "bitrix24")
            return False
