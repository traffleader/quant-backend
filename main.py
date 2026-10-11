from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

app = FastAPI(title="Quant PRO API")

# Разрешаем доступ со всех источников (включая ваш Mini App на Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Состояние рынка в памяти
market_state: Dict[str, Dict[str, Any]] = {
    "EURUSD": {
        "status": "BULLISH",
        "verdict": "STRONG BUY",
        "price": 1.0837,
        "change24h": "+0.42%",
        "volatility": "High ATR",
        "synergy": 85,
        "eq_pro": {"lppl": "STABLE / NO BUBBLE", "hurst": 0.62},
        "hqn": {"adx": 32, "atr": "HIGH", "score": 88},
        "killzone": {"active": "London Killzone", "time_remaining": "01:24:10"}
    }
}

@app.get("/api/market-state")
async def get_market_state(pair: str = "EURUSD"):
    return market_state.get(pair, {"error": "Pair not found"})

@app.post("/api/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    pair = data.get("pair", "EURUSD")
    
    if pair not in market_state:
        market_state[pair] = {}
        
    payload = data.get("payload", {})
    market_state[pair].update(payload)
    
    return {"status": "success", "pair": pair, "updated": payload}
