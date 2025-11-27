import os
import json
import time
import re
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
import mysql.connector

# Если измените эти SCOPES, удалите файл token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Определяем базовую директорию как директорию, в которой находится текущий файл
BASE_DIR = Path(__file__).resolve().parent

# Пути к файлам токенов и секретов
KEY_TOKEN = BASE_DIR / 'keys_json' / 'token.json'
KEY_SECRET = BASE_DIR / 'keys_json' / 'client_secret.json'

# Подключение к базе данных
def connect_db():
    dbconfig = {
            'host': '45.12.18.215',
            'user': 'test',
            'password': 'Themoon13!',
            'database': 'test'
    }
    return mysql.connector.connect(**dbconfig)


# Проверка состояния функции
def is_function_active():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM func_status ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else False

# Запись истории выполнения функции
def create_notion_history(status, request_time):
    conn = connect_db()
    cursor = conn.cursor()
    folder = str(Path(__file__).resolve().parent)
    query = "INSERT INTO history_query (status, folder, request_time) VALUES (%s, %s, %s)"
    cursor.execute(query, (status, folder, request_time))
    conn.commit()
    cursor.close()
    conn.close()

# Установка нового статуса функции
def set_function_status(status, request_time):
    conn = connect_db()
    cursor = conn.cursor()
    query = "INSERT INTO func_status (status, timestamp) VALUES (%s, %s)"
    cursor.execute(query, (status, request_time))
    conn.commit()
    cursor.close()
    conn.close()

    create_notion_history(status, request_time)

# Аутентификация Gmail
def authenticate_gmail():
    creds = None
    # Получение токена из файла
    if os.path.exists(KEY_TOKEN):
        creds = Credentials.from_authorized_user_file(KEY_TOKEN, SCOPES)
    
    # Проверка валидности токена
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(KEY_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
            # Сохранение нового токена в файл
            with open(KEY_TOKEN, 'w') as token:
                token.write(creds.to_json())
    
    return creds

# Получение 2FA-кода
def list_messages(service, user_id='me', request_time=datetime.now()):
    request_time = request_time.replace(tzinfo=timezone.utc)
    try:
        set_function_status('active', request_time)
        for i in range(6):
            results = service.users().messages().list(userId=user_id).execute()
            messages = results.get('messages', [])
            if not messages:
                print('No messages found.')
            else:
                for message in messages[:5]:
                    msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
                    if 'Rocket Tech School' in msg['snippet']: 
                        internal_date = msg.get('internalDate')
                        if internal_date:
                            message_time = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc)
                            time_difference = (request_time - message_time).total_seconds()
                            if -10 <= time_difference <= 60:
                                match = re.search(r'authorization code: (\d+)', msg['snippet'])
                                if match:
                                    return match.group(1)

            print(f'Кода не найдено. Попытка {i} +')
            time.sleep(10)

        set_function_status('time_error', request_time)
    except Exception as error:
        print(f'An error occurred: {error}')
        set_function_status('inactive', request_time)
    finally:
        set_function_status('inactive', request_time)

def get_2fa_code(request_time):
    for attempt in range(10):  # Попытка до 10 раз
        if is_function_active() != 'active':  # Проверка статуса функции
            creds = authenticate_gmail()
            service = build('gmail', 'v1', credentials=creds)
            code = list_messages(service, request_time=request_time)
            return code  # Если код найден, возвращаем его
        else:
            print(f'Функция занята другой программой. Попытка {attempt}')
            time.sleep(10)  # Ожидание 10 секунд перед повторной попыткой
           

    print('Код не был найден после 10 попыток.')
    return None  # Если код не был найден после 10 попыт
