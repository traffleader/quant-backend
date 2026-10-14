from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

app = FastAPI()


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


storage = {}


@app.post("/api/webhook")
async def receive_webhook(payload: EmeraldPayload):
    try:
        storage[payload.pair.upper()] = payload.dict()
        print(f"✅ Данные обновлены для {payload.pair} | Вердикт: {payload.synergy.verdict}")
        return {"status": "success", "pair": payload.pair}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/{pair}")
async def get_pair_data(pair: str):
    """Отдает актуальные метрики по паре для Telegram Mini App"""
    pair_upper = pair.upper()
    if pair_upper in storage:
        return storage[pair_upper]
    raise HTTPException(status_code=404, detail="Пара не найдена")


@app.get("/api/card/{pair}")
async def get_pair_card(pair: str):
    """Генерирует и возвращает визуальную карточку аналитики"""
    pair_upper = pair.upper()
    if pair_upper not in storage:
        raise HTTPException(status_code=404, detail="Пара не найдена")

    data = storage[pair_upper]

    # Создаем холст в темном трейдерском стиле
    width, height = 700, 450
    img = Image.new("RGB", (width, height), color="#121316")
    draw = ImageDraw.Draw(img)

    # Загрузка шрифтов с fallback на дефолтный
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_bold = ImageFont.truetype("arial.ttf", 18)
        font_regular = ImageFont.truetype("arial.ttf", 15)
    except:
        font_title = font_bold = font_regular = ImageFont.load_default()

    # Шапка карточки
    action_color = "#00FF66" if data["synergy"]["action"] == "BUY" else "#FF3B30"
    draw.rectangle([(0, 0), (width, 8)], fill=action_color)
    draw.text((30, 20), f"{data['pair']} — ANALYTICAL CARD", fill="#FFFFFF", font=font_title)
    draw.text((500, 25), f"PRICE: {data['price']}", fill="#00E5FF", font=font_bold)

    # Блок метрик (сетка 2x3)
    metrics = data["metrics"]
    m_list = [
        ("HTF Trend", metrics["trend_htf"]),
        ("Hurst Index", str(metrics["hurst"])),
        ("Entry Dist", metrics["entry_dist"]),
        ("LPPL State", metrics["lppl_state"]),
        ("Zone Status", metrics["zone_status"]),
        ("Info Ratio", str(metrics["info_ratio"])),
    ]

    x, y = 30, 95
    for i, (label, val) in enumerate(m_list):
        draw.rounded_rectangle([(x, y), (x + 310, y + 60)], radius=8, fill="#1E222D")
        draw.text((x + 15, y + 10), label.upper(), fill="#848E9C", font=font_regular)
        draw.text((x + 15, y + 32), str(val), fill="#FFFFFF", font=font_bold)
        
        x += 330
        if (i + 1) % 2 == 0:
            x = 30
            y += 75

    # Блок вердикта внизу
    synergy = data["synergy"]
    draw.rounded_rectangle([(30, 355), (670, 420)], radius=8, fill="#1B1F2A")
    draw.text((50, 375), f"VERDICT: {synergy['verdict']}", fill="#00FF66", font=font_bold)
    draw.text((520, 375), f"SCORE: {synergy['score']}/100", fill="#FFD700", font=font_bold)

    # Сохранение в буфер памяти и отправка
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
