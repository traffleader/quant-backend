from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Quant PRO API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Память сервера для хранения текущего состояния рынка
current_market_data = {
    "pair": "EURUSD",
    "status": "BULLISH",
    "verdict": "STRONG BUY",
    "price": 1.0837,
    "change24h": "+0.42%",
    "volatility": "High ATR",
    "synergy": 85,
    "eq_pro": {
        "lpp1": "STABLE / NO BUBBLE",
        "hurst": 0.62
    },
    "hqn": {
        "adx": 32,
        "atr": "HIGH",
        "score": 88
    },
    "killzone": {
        "active": "London Killzone",
        "time_remaining": "01:24:10"
    }
}

@app.get("/api/market-state")
def get_market_state(pair: str = "EURUSD"):
    # Отдает актуальные данные фронтенду в Telegram Mini App
    return current_market_data

@app.post("/api/webhook")
def receive_webhook(payload: dict):
    global current_market_data
    # Принимает новые данные от вашего скрипта и обновляет состояние
    current_market_data.update(payload)
    return {"status": "success", "received": payload}
