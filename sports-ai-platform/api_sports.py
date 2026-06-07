import os
import requests
from datetime import datetime

API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

def _request_json(url):
    if not API_KEY:
        raise ValueError("找不到 API_FOOTBALL_KEY，請確認環境變數或 GitHub Codespaces Secret。")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    if response.status_code != 200:
        raise RuntimeError(f"API 回傳錯誤狀態碼：{response.status_code}")

    return response.json()

def get_live_football():
    return _request_json("https://v3.football.api-sports.io/fixtures?live=all")

def get_football_by_date(date_str):
    return _request_json(f"https://v3.football.api-sports.io/fixtures?date={date_str}")

def get_live_baseball():
    return _request_json("https://v1.baseball.api-sports.io/games?live=all")

def get_baseball_by_date(date_str):
    return _request_json(f"https://v1.baseball.api-sports.io/games?date={date_str}")

def get_today_baseball():
    today = datetime.now().strftime("%Y-%m-%d")
    return get_baseball_by_date(today)

def get_live_basketball():
    return _request_json("https://v1.basketball.api-sports.io/games?live=all")

def get_basketball_by_date(date_str):
    return _request_json(f"https://v1.basketball.api-sports.io/games?date={date_str}")
