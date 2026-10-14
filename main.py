from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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
    """Отдает актуальные метрики в формате JSON для Mini App"""
    pair_upper = pair.upper()
    if pair_upper in storage:
        return storage[pair_upper]
    # Возвращаем дефолтную заглушку, если пара еще не прилетела
    return {
        "pair": pair_upper,
        "price": 0.0,
        "metrics": {
            "trend_htf": "WAIT",
            "hurst": 0.5,
            "entry_dist": "0.0%",
            "lppl_state": "WAIT",
            "zone_status": "WAIT",
            "info_ratio": 0.0
        },
        "synergy": {"verdict": "WAITING DATA", "action": "WAIT", "score": 0}
    }


@app.get("/api/card/{pair}")
async def get_pair_card(pair: str):
    """Генерирует PNG карточку (опционально для отправки в чат)"""
    pair_upper = pair.upper()
    if pair_upper not in storage:
        raise HTTPException(status_code=404, detail="Пара не найдена")

    data = storage[pair_upper]
    width, height = 700, 450
    img = Image.new("RGB", (width, height), color="#121316")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_bold = ImageFont.truetype("arial.ttf", 18)
        font_regular = ImageFont.truetype("arial.ttf", 15)
    except:
        font_title = font_bold = font_regular = ImageFont.load_default()

    action_color = "#00FF66" if data["synergy"]["action"] == "BUY" else ("#FF3B30" if data["synergy"]["action"] == "SELL" else "#FFD700")
    draw.rectangle([(0, 0), (width, 8)], fill=action_color)
    draw.text((30, 20), f"{data['pair']} — QUANTUM TERMINAL", fill="#FFFFFF", font=font_title)
    draw.text((470, 25), f"PRICE: {data['price']}", fill="#00E5FF", font=font_bold)

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

    synergy = data["synergy"]
    draw.rounded_rectangle([(30, 355), (670, 420)], radius=8, fill="#1B1F2A")
    draw.text((50, 375), f"VERDICT: {synergy['verdict']}", fill=action_color, font=font_bold)
    draw.text((520, 375), f"SCORE: {synergy['score']}/100", fill="#FFD700", font=font_bold)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/", response_class=HTMLResponse)
async def serve_mini_app():
    """Интерфейс Telegram Mini App (HTML/Tailwind)"""
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emerald Quantum Mini App</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { background-color: #0d1117; color: #f3f4f6; }
        .glass { background: rgba(30, 34, 45, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-buy { box-shadow: 0 0 25px rgba(0, 255, 102, 0.15); border-color: rgba(0, 255, 102, 0.4); }
        .glow-sell { box-shadow: 0 0 25px rgba(255, 59, 48, 0.15); border-color: rgba(255, 59, 48, 0.4); }
    </style>
</head>
<body class="p-4 max-w-md mx-auto min-h-screen flex flex-col justify-between">
    <div>
        <!-- Шапка -->
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-xl font-bold tracking-wider text-cyan-400">EMERALD QUANT</h1>
                <p class="text-xs text-gray-400">Autonomous Trading Pipeline</p>
            </div>
            <div id="pair-badge" class="px-3 py-1 rounded-lg bg-gray-800 text-sm font-semibold border border-gray-700">EURGBP</div>
        </div>

        <!-- Переключатель пар -->
        <div class="grid grid-cols-3 gap-2 mb-6">
            <button onclick="changePair('EURGBP')" class="py-2 rounded-lg bg-cyan-600 font-medium text-sm transition active:scale-95" id="btn-eurgbp">EURGBP</button>
            <button onclick="changePair('BTCUSD')" class="py-2 rounded-lg bg-gray-800 font-medium text-sm text-gray-400 transition active:scale-95" id="btn-btcusd">BTCUSD</button>
            <button onclick="changePair('XAUUSD')" class="py-2 rounded-lg bg-gray-800 font-medium text-sm text-gray-400 transition active:scale-95" id="btn-xauusd">XAUUSD</button>
        </div>

        <!-- Основная карточка цены -->
        <div id="main-card" class="glass rounded-2xl p-5 mb-5 transition-all duration-300">
            <div class="flex justify-between items-center mb-4">
                <span class="text-xs uppercase tracking-widest text-gray-400">Live Price</span>
                <span id="price-val" class="text-2xl font-black text-cyan-300">0.00000</span>
            </div>

            <!-- Сетка метрик -->
            <div class="grid grid-cols-2 gap-3 mb-4">
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">HTF Trend</div>
                    <div id="m-trend" class="text-base font-bold mt-1">-</div>
                </div>
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">Hurst Index</div>
                    <div id="m-hurst" class="text-base font-bold mt-1">-</div>
                </div>
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">Entry Dist</div>
                    <div id="m-dist" class="text-base font-bold mt-1">-</div>
                </div>
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">LPPL State</div>
                    <div id="m-lppl" class="text-base font-bold mt-1">-</div>
                </div>
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">Zone Status</div>
                    <div id="m-zone" class="text-base font-bold mt-1">-</div>
                </div>
                <div class="bg-gray-900/60 p-3 rounded-xl border border-gray-800">
                    <div class="text-[10px] uppercase text-gray-500">Info Ratio</div>
                    <div id="m-ir" class="text-base font-bold mt-1">-</div>
                </div>
            </div>

            <!-- Вердикт -->
            <div class="bg-gray-900/80 p-4 rounded-xl flex justify-between items-center border border-gray-800">
                <div>
                    <div class="text-[10px] text-gray-500 uppercase">Synergy Verdict</div>
                    <div id="v-text" class="text-sm font-black tracking-wide mt-0.5">-</div>
                </div>
                <div class="text-right">
                    <div class="text-[10px] text-gray-500 uppercase">Score</div>
                    <div id="v-score" class="text-lg font-black text-amber-400">-</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Футер / Кнопка -->
    <div class="text-center pb-4">
        <button onclick="fetchData()" class="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 font-bold text-white shadow-lg active:scale-95 transition">Обновить данные</button>
        <p class="text-[10px] text-gray-500 mt-3">Emerald Quantum Engine v14.6 • Render Cloud</p>
    </div>

    <script>
        let currentPair = 'EURGBP';

        function changePair(pair) {
            currentPair = pair;
            ['eurgbp', 'btcusd', 'xauusd'].forEach(p => {
                const btn = document.getElementById(`btn-${p}`);
                if (p === pair.toLowerCase()) {
                    btn.className = "py-2 rounded-lg bg-cyan-600 font-medium text-sm transition active:scale-95";
                } else {
                    btn.className = "py-2 rounded-lg bg-gray-800 font-medium text-sm text-gray-400 transition active:scale-95";
                }
            });
            document.getElementById('pair-badge').innerText = pair;
            fetchData();
        }

        async function fetchData() {
            try {
                const res = await fetch(`/api/data/${currentPair}`);
                if (!res.ok) return;
                const data = await res.json();

                document.getElementById('price-val').innerText = data.price;
                document.getElementById('m-trend').innerText = data.metrics.trend_htf;
                document.getElementById('m-hurst').innerText = data.metrics.hurst;
                document.getElementById('m-dist').innerText = data.metrics.entry_dist;
                document.getElementById('m-lppl').innerText = data.metrics.lppl_state;
                document.getElementById('m-zone').innerText = data.metrics.zone_status;
                document.getElementById('m-ir').innerText = data.metrics.info_ratio;

                document.getElementById('v-text').innerText = data.synergy.verdict;
                document.getElementById('v-score').innerText = data.synergy.score + '/100';

                const card = document.getElementById('main-card');
                card.className = "glass rounded-2xl p-5 mb-5 transition-all duration-300 " + 
                    (data.synergy.action === 'BUY' ? 'glow-buy' : (data.synergy.action === 'SELL' ? 'glow-sell' : ''));
                
                const vText = document.getElementById('v-text');
                vText.style.color = data.synergy.action === 'BUY' ? '#00FF66' : (data.synergy.action === 'SELL' ? '#FF3B30' : '#FFD700');
            } catch (e) {
                console.error(e);
            }
        }

        // Автообновление каждые 10 секунд
        setInterval(fetchData, 10000);
        fetchData();
    </script>
</body>
</html>
    """
