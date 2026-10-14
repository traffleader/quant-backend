from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Pydantic-модели для строгой валидации входящих данных от TradingView / скрипта
class Metrics(BaseModel):
    trend_htf: str
    hurst: float
    entry_dist: str
    lppl_state: str
    zone_status: str
    info_ratio: float

class Synergy(BaseModel):
    verdict: str
    action: str
    score: int

class EmeraldPayload(BaseModel):
    pair: str
    price: float
    metrics: Metrics
    synergy: Synergy

# Временное хранилище в памяти для последней аналитики по парам
storage = {}

@app.post("/api/webhook")
async def receive_webhook(payload: EmeraldPayload):
    try:
        # Сохраняем актуальный слепок данных по конкретной торговой паре
        storage[payload.pair] = payload.dict()
        print(f"✅ Данные обновлены для {payload.pair} | Вердикт: {payload.synergy.verdict}")
        return {"status": "success", "pair": payload.pair}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/data/{pair}")
async def get_pair_data(pair: str):
    """Эндпоинт для Telegram Mini App: отдает актуальные метрики по паре"""
    if pair in storage:
        return storage[pair]
    return {"error": "Пара не найдена или данные еще не поступали"}

@app.get("/api/data")
async def get_all_data():
    """Эндпоинт для получения всей доступной аналитики"""
    return storage
