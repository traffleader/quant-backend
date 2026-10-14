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
        # Нормализуем название пары со слэшем (например, EURGBP -> EUR/GBP)
        pair_raw = payload.pair.upper().replace("/", "")
        if len(pair_raw) == 6:
            formatted_pair = f"{pair_raw[:3]}/{pair_raw[3:]}"
        else:
            formatted_pair = payload.pair.upper()
            
        data = payload.dict()
        data["pair"] = formatted_pair
        storage[formatted_pair] = data
        print(f"✅ Данные обновлены для {formatted_pair} | Вердикт: {payload.synergy.verdict}")
        return {"status": "success", "pair": formatted_pair}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/data/{pair}")
async def get_pair_data(pair: str):
    # Принимаем пару в формате EUR/GBP или EURGBP
    pair_clean = pair.upper().replace("/", "")
    if len(pair_clean) == 6:
        formatted_pair = f"{pair_clean[:3]}/{pair_clean[3:]}"
    else:
        formatted_pair = pair.upper()
        
    if formatted_pair in storage:
        return storage[formatted_pair]
    return {
        "pair": formatted_pair,
        "price": 0.0,
        "metrics": {
            "trend_htf": "WAIT",
            "hurst": 0.5,
            "entry_dist": "0.0%",
            "lppl_state": "WAIT",
            "zone_status": "WAIT",
            "info_ratio": 0.0
        },
        "synergy": {"verdict": "NEUTRAL WAIT", "action": "WAIT", "score": 50}
    }

@app.get("/", response_class=HTMLResponse)
async def serve_mini_app():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quant PRO Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { background-color: #080c10; color: #f3f4f6; font-family: 'Plus Jakarta Sans', sans-serif; }
        .glass-card { background: linear-gradient(135deg, rgba(16, 22, 34, 0.85) 0%, rgba(10, 14, 22, 0.95) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.07); }
        .glow-buy { box-shadow: 0 0 35px rgba(0, 255, 136, 0.15); border-color: rgba(0, 255, 136, 0.4); background: linear-gradient(145deg, rgba(12, 30, 24, 0.9) 0%, rgba(8, 14, 20, 0.95) 100%); }
        .glow-sell { box-shadow: 0 0 35px rgba(255, 59, 48, 0.15); border-color: rgba(255, 59, 48, 0.4); background: linear-gradient(145deg, rgba(35, 15, 20, 0.9) 0%, rgba(8, 14, 20, 0.95) 100%); }
        .active-tab { background: linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(0, 153, 255, 0.08) 100%); border: 1px solid rgba(0, 229, 255, 0.5); box-shadow: 0 0 20px rgba(0, 229, 255, 0.15); }
    </style>
</head>
<body class="pb-24 max-w-md mx-auto min-h-screen flex flex-col justify-between selection:bg-cyan-500 selection:text-white">
    
    <!-- Верхняя шапка -->
    <div class="p-4">
        <div class="flex justify-between items-center mb-4">
            <div class="flex items-center space-x-2.5">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-teal-400 to-emerald-400 flex items-center justify-center shadow-lg shadow-cyan-500/25">
                    <svg class="w-5 h-5 text-gray-950" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                </div>
                <div>
                    <h1 class="text-base font-extrabold tracking-tight text-white flex items-center gap-1.5">
                        Quant <span class="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300">PRO</span>
                    </h1>
                    <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">ANALYTICS</p>
                </div>
            </div>
            <div class="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold flex items-center gap-1.5 shadow-sm shadow-emerald-500/10">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Участник Клуба
            </div>
        </div>

        <!-- Переключатель пар со слэшем -->
        <div class="grid grid-cols-3 gap-2 mb-5">
            <button onclick="changePair('EUR/GBP')" id="btn-EUR/GBP" class="py-2.5 px-2 rounded-xl active-tab text-cyan-300 font-extrabold text-xs transition active:scale-95 flex flex-col items-center">
                <span>EUR/GBP</span>
                <span class="text-[10px] text-emerald-400 font-semibold mt-0.5">+0.42%</span>
            </button>
            <button onclick="changePair('BTC/USD')" id="btn-BTC/USD" class="py-2.5 px-2 rounded-xl glass-card text-gray-400 font-semibold text-xs transition active:scale-95 flex flex-col items-center">
                <span>BTC/USD</span>
                <span class="text-[10px] text-emerald-400 font-semibold mt-0.5">+1.84%</span>
            </button>
            <button onclick="changePair('XAU/USD')" id="btn-XAU/USD" class="py-2.5 px-2 rounded-xl glass-card text-gray-400 font-semibold text-xs transition active:scale-95 flex flex-col items-center">
                <span>XAU/USD</span>
                <span class="text-[10px] text-rose-400 font-semibold mt-0.5">-0.15%</span>
            </button>
        </div>

        <!-- КОНТЕНТ ВКЛАДКИ: ТЕРМИНАЛ -->
        <div id="tab-terminal" class="space-y-4">
            <!-- Основная карточка цены и вердикта -->
            <div id="main-card" class="glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden">
                <!-- Декоративный градиентный засвет на фоне карточки -->
                <div class="absolute -right-10 -top-10 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none"></div>

                <div class="flex justify-between items-center mb-2">
                    <span class="text-[11px] font-bold tracking-wider text-gray-400 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-400"></span> ПРЯМО СЕЙЧАС
                    </span>
                    <span id="badge-trend" class="px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-extrabold tracking-wide flex items-center gap-1">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg> БЫЧИЙ ТРЕНД
                    </span>
                </div>

                <div class="mb-4">
                    <h2 id="pair-title" class="text-2xl font-black text-white tracking-tight">EUR/GBP</h2>
                    <div class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-teal-300 to-emerald-300 mt-1 flex items-baseline gap-2">
                        <span id="price-val">0.00000</span>
                        <span class="text-xs font-extrabold text-emerald-400">+0.42%</span>
                    </div>
                </div>

                <!-- Блок вердикта со шкалой -->
                <div class="bg-gray-950/70 p-4 rounded-xl border border-gray-800/80 shadow-inner">
                    <div class="text-[10px] font-extrabold uppercase tracking-widest text-gray-400 mb-1">Вердикт алгоритма</div>
                    <div id="v-text" class="text-lg font-black text-emerald-400 tracking-wide">СИЛЬНЫЙ ПОКУПАТЬ</div>
                    
                    <div class="flex justify-between items-center mt-3 text-xs text-gray-400 font-medium">
                        <span>До зоны входа</span>
                        <span id="m-dist" class="font-bold text-white">0.05%</span>
                    </div>
                    <div class="w-full bg-gray-900 h-2.5 rounded-full mt-2 overflow-hidden p-0.5 border border-gray-800">
                        <div id="progress-bar" class="bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 h-full w-3/4 rounded-full transition-all duration-500 shadow-sm shadow-emerald-400/50"></div>
                    </div>
                </div>
            </div>

            <!-- Сетка метрик -->
            <div class="grid grid-cols-2 gap-3">
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Индекс Херста</div>
                    <div id="m-hurst" class="text-xl font-black text-white">0.58</div>
                    <div class="text-[10px] font-semibold text-cyan-400 mt-0.5">Трендовый режим</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Information Ratio</div>
                    <div id="m-ir" class="text-xl font-black text-emerald-400">+0.14</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Эффективность</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Модель Сорнетте</div>
                    <div id="m-lppl" class="text-base font-black text-emerald-400">СТАБИЛЬНО</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Нет риска пузыря</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Синергия сети</div>
                    <div id="v-score" class="text-xl font-black text-amber-400">88/100</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Высокая точность</div>
                </div>
            </div>
        </div>

        <!-- КОНТЕНТ ВКЛАДКИ: СЕССИИ (СКРЫТО ПО УМОЛЧАНИЮ) -->
        <div id="tab-sessions" class="space-y-4 hidden">
            <div class="glass-card rounded-2xl p-4">
                <h3 class="text-sm font-extrabold text-white mb-1">Сессии и ICT Killzones</h3>
                <p class="text-[11px] text-gray-400 mb-4 font-medium">Время мировых бирж · UTC</p>
                
                <div class="space-y-2.5">
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400"></span> Сидней</span>
                        <span class="text-xs font-extrabold text-emerald-400">АКТИВНО</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400"></span> Токио</span>
                        <span class="text-xs font-extrabold text-emerald-400">АКТИВНО</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-gray-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-gray-600"></span> Лондон</span>
                        <span class="text-xs font-semibold text-gray-500">—</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-gray-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-gray-600"></span> Нью-Йорк</span>
                        <span class="text-xs font-semibold text-gray-500">—</span>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- Нижняя панель навигации -->
    <div class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-[#070b0f]/95 backdrop-blur-2xl border-t border-gray-800/80 px-6 py-3 flex justify-between items-center z-50">
        <button onclick="switchTab('terminal')" id="nav-terminal" class="flex flex-col items-center gap-1 text-cyan-400 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            <span class="text-[10px] font-bold">Терминал</span>
        </button>
        <button onclick="switchTab('sessions')" id="nav-sessions" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span class="text-[10px] font-semibold">Сессии</span>
        </button>
        <button onclick="alert('Раздел сигналов в разработке')" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            <span class="text-[10px] font-semibold">Сигналы</span>
        </button>
        <button onclick="alert('Настройки аккаунта Клуба')" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.08 1.97.53 2.572 1.065z"></path></svg>
            <span class="text-[10px] font-semibold">Настройки</span>
        </button>
    </div>

    <script>
        let currentPair = 'EUR/GBP';

        function switchTab(tab) {
            if (tab === 'terminal') {
                document.getElementById('tab-terminal').classList.remove('hidden');
                document.getElementById('tab-sessions').classList.add('hidden');
                document.getElementById('nav-terminal').className = "flex flex-col items-center gap-1 text-cyan-400 transition";
                document.getElementById('nav-sessions').className = "flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition";
            } else {
                document.getElementById('tab-terminal').classList.add('hidden');
                document.getElementById('tab-sessions').classList.remove('hidden');
                document.getElementById('nav-sessions').className = "flex flex-col items-center gap-1 text-cyan-400 transition";
                document.getElementById('nav-terminal').className = "flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition";
            }
        }

        function changePair(pair) {
            currentPair = pair;
            ['EUR/GBP', 'BTC/USD', 'XAU/USD'].forEach(p => {
                const btnId = p.replace('/', '');
                const btn = document.getElementById(`btn-${p}`);
                if (p === pair) {
                    btn.className = "py-2.5 px-2 rounded-xl active-tab text-cyan-300 font-extrabold text-xs transition active:scale-95 flex flex-col items-center";
                } else {
                    btn.className = "py-2.5 px-2 rounded-xl glass-card text-gray-400 font-semibold text-xs transition active:scale-95 flex flex-col items-center";
                }
            });
            document.getElementById('pair-title').innerText = pair;
            fetchData();
        }

        async function fetchData() {
            try {
                const res = await fetch(`/api/data/${encodeURIComponent(currentPair)}`);
                if (!res.ok) return;
                const data = await res.json();

                document.getElementById('price-val').innerText = data.price;
                document.getElementById('m-hurst').innerText = data.metrics.hurst;
                document.getElementById('m-dist').innerText = data.metrics.entry_dist;
                document.getElementById('m-lppl').innerText = data.metrics.lppl_state;
                document.getElementById('m-ir').innerText = data.metrics.info_ratio;
                document.getElementById('v-score').innerText = data.synergy.score + '/100';

                const vText = document.getElementById('v-text');
                vText.innerText = data.synergy.verdict;
                
                const card = document.getElementById('main-card');
                const badgeTrend = document.getElementById('badge-trend');

                if (data.synergy.action === 'BUY') {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden glow-buy";
                    vText.style.color = '#00ff88';
                    badgeTrend.innerText = 'БЫЧИЙ ТРЕНД';
                    badgeTrend.className = "px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-extrabold tracking-wide flex items-center gap-1";
                } else if (data.synergy.action === 'SELL') {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden glow-sell";
                    vText.style.color = '#ff3b30';
                    badgeTrend.innerText = 'МЕДВЕЖИЙ ТРЕНД';
                    badgeTrend.className = "px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-400 text-xs font-extrabold tracking-wide flex items-center gap-1";
                } else {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden";
                    vText.style.color = '#ffd700';
                    badgeTrend.innerText = 'ОЖИДАНИЕ';
                    badgeTrend.className = "px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/40 text-amber-400 text-xs font-extrabold tracking-wide flex items-center gap-1";
                }
            } catch (e) {
                console.error(e);
            }
        }

        setInterval(fetchData, 10000);
        fetchData();
    </script>
</body>
</html>
    """
