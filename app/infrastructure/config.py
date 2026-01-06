
import os
import sys
import json

CONFIG_FILE = 'config.json'
def get_config_path():
    # Путь к файлу config.json рядом с exe
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), CONFIG_FILE)
    return os.path.join(os.path.dirname(__file__), CONFIG_FILE)

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(data: dict):
    path = get_config_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_or_ask(key: str, prompt: str) -> str:
    config = load_config()
    if key not in config or not config[key].strip():
        config[key] = input(prompt).strip()
        save_config(config)
    return config[key]


ALLOWED_USER_ID = get_or_ask('telegram_user_id', 'Введіть id телеграм користувача: ')
TOKEN = get_or_ask('telegram_token', 'Введіть токен телеграм бота: ')

