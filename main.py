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
    pair_upper = pair.upper()
    if pair_upper in storage:
        return storage[pair_upper]
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
        "synergy": {"verdict": "WAITING DATA", "action": "WAIT", "score": 50}
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
    <style>
        body { background-color: #0b0f15; color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .glass-card { background: rgba(18, 22, 31, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.06); }
        .glow-buy { box-shadow: 0 0 30px rgba(0, 255, 136, 0.12); border-color: rgba(0, 255, 136, 0.35); }
        .glow-sell { box-shadow: 0 0 30px rgba(255, 59, 48, 0.12); border-color: rgba(255, 59, 48, 0.35); }
        .active-tab { background: linear-gradient(135deg, rgba(0, 229, 255, 0.15), rgba(0, 153, 255, 0.05)); border: 1px solid rgba(0, 229, 255, 0.4); }
    </style>
</head>
<body class="pb-24 max-w-md mx-auto min-h-screen flex flex-col justify-between selection:bg-cyan-500 selection:text-white">
    
    <!-- Верхняя шапка -->
    <div class="p-4">
        <div class="flex justify-between items-center mb-4">
            <div class="flex items-center space-x-2">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-emerald-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                    <svg class="w-5 h-5 text-gray-950" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                </div>
                <div>
                    <h1 class="text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                        Quant <span class="text-cyan-400">PRO</span>
                    </h1>
                    <p class="text-[10px] text-gray-400 uppercase tracking-widest">Analytics</p>
                </div>
            </div>
            <div class="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-semibold flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Участник Клуба
            </div>
        </div>

        <!-- Переключатель пар -->
        <div class="grid grid-cols-3 gap-2 mb-5">
            <button onclick="changePair('EURGBP')" id="btn-eurgbp" class="py-2.5 px-3 rounded-xl active-tab text-cyan-300 font-bold text-xs transition active:scale-95 flex flex-col items-center">
                <span>EURGBP</span>
                <span class="text-[10px] text-emerald-400 font-normal mt-0.5">+0.42%</span>
            </button>
            <button onclick="changePair('BTCUSD')" id="btn-btcusd" class="py-2.5 px-3 rounded-xl glass-card text-gray-400 font-medium text-xs transition active:scale-95 flex flex-col items-center">
                <span>BTCUSD</span>
                <span class="text-[10px] text-emerald-400 font-normal mt-0.5">+1.84%</span>
            </button>
            <button onclick="changePair('XAUUSD')" id="btn-xauusd" class="py-2.5 px-3 rounded-xl glass-card text-gray-400 font-medium text-xs transition active:scale-95 flex flex-col items-center">
                <span>XAUUSD</span>
                <span class="text-[10px] text-rose-400 font-normal mt-0.5">-0.15%</span>
            </button>
        </div>

        <!-- КОНТЕНТ ВКЛАДКИ: ТЕРМИНАЛ -->
        <div id="tab-terminal" class="space-y-4">
            <!-- Основная карточка цены и вердикта -->
            <div id="main-card" class="glass-card rounded-2xl p-5 transition-all duration-300">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-[11px] font-medium tracking-wider text-gray-400 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span> ПРЯМО СЕЙЧАС
                    </span>
                    <span id="badge-trend" class="px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold">БЫЧИЙ ТРЕНД</span>
                </div>

                <div class="mb-4">
                    <h2 id="pair-title" class="text-2xl font-black text-white tracking-tight">EURGBP</h2>
                    <div class="text-3xl font-black text-cyan-400 mt-1 flex items-baseline gap-2">
                        <span id="price-val">0.00000</span>
                        <span class="text-xs font-semibold text-emerald-400">+0.42%</span>
                    </div>
                </div>

                <!-- Блок вердикта со шкалой -->
                <div class="bg-gray-900/70 p-4 rounded-xl border border-gray-800/80">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Вердикт алгоритма</div>
                    <div id="v-text" class="text-lg font-black text-emerald-400 tracking-wide">СИЛЬНЫЙ ПОКУПАТЬ</div>
                    
                    <div class="flex justify-between items-center mt-3 text-xs text-gray-400">
                        <span>До зоны входа</span>
                        <span id="m-dist" class="font-bold text-white">0.05%</span>
                    </div>
                    <div class="w-full bg-gray-800 h-2 rounded-full mt-1.5 overflow-hidden">
                        <div id="progress-bar" class="bg-gradient-to-r from-cyan-500 to-emerald-400 h-full w-3/4 rounded-full transition-all duration-500"></div>
                    </div>
                </div>
            </div>

            <!-- Сетка метрик -->
            <div class="grid grid-cols-2 gap-3">
                <div class="glass-card p-4 rounded-2xl">
                    <div class="text-[10px] uppercase font-semibold text-gray-400 mb-1">Индекс Херста</div>
                    <div id="m-hurst" class="text-lg font-black text-white">0.58</div>
                    <div class="text-[10px] text-cyan-400 mt-0.5">Трендовый режим</div>
                </div>
                <div class="glass-card p-4 rounded-2xl">
                    <div class="text-[10px] uppercase font-semibold text-gray-400 mb-1">Information Ratio</div>
                    <div id="m-ir" class="text-lg font-black text-emerald-400">+0.14</div>
                    <div class="text-[10px] text-gray-400 mt-0.5">Эффективность</div>
                </div>
                <div class="glass-card p-4 rounded-2xl">
                    <div class="text-[10px] uppercase font-semibold text-gray-400 mb-1">Модель Сорнетте</div>
                    <div id="m-lppl" class="text-base font-black text-emerald-400">СТАБИЛЬНО</div>
                    <div class="text-[10px] text-gray-400 mt-0.5">Нет риска пузыря</div>
                </div>
                <div class="glass-card p-4 rounded-2xl">
                    <div class="text-[10px] uppercase font-semibold text-gray-400 mb-1">Синергия сети</div>
                    <div id="v-score" class="text-lg font-black text-amber-400">88/100</div>
                    <div class="text-[10px] text-gray-400 mt-0.5">Высокая точность</div>
                </div>
            </div>
        </div>

        <!-- КОНТЕНТ ВКЛАДКИ: СЕССИИ (СКРЫТО ПО УМОЛЧАНИЮ) -->
        <div id="tab-sessions" class="space-y-4 hidden">
            <div class="glass-card rounded-2xl p-4">
                <h3 class="text-sm font-bold text-white mb-1">Сессии и ICT Killzones</h3>
                <p class="text-[11px] text-gray-400 mb-4">Время мировых бирж по UTC</p>
                
                <div class="space-y-2.5">
                    <div class="flex justify-between items-center bg-gray-900/50 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-semibold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400"></span> Сидней</span>
                        <span class="text-xs font-bold text-emerald-400">АКТИВНО</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-900/50 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-semibold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400"></span> Токио</span>
                        <span class="text-xs font-bold text-emerald-400">АКТИВНО</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-900/50 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-semibold text-gray-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-gray-600"></span> Лондон</span>
                        <span class="text-xs font-semibold text-gray-500">—</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-900/50 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-semibold text-gray-400 flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-gray-600"></span> Нью-Йорк</span>
                        <span class="text-xs font-semibold text-gray-500">—</span>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- Нижняя панель навигации (как в лучших приложениях) -->
    <div class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-[#0b0f15]/95 backdrop-blur-xl border-t border-gray-800/80 px-6 py-3 flex justify-between items-center z-50">
        <button onclick="switchTab('terminal')" id="nav-terminal" class="flex flex-col items-center gap-1 text-cyan-400 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            <span class="text-[10px] font-bold">Терминал</span>
        </button>
        <button onclick="switchTab('sessions')" id="nav-sessions" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span class="text-[10px] font-medium">Сессии</span>
        </button>
        <button onclick="alert('Раздел сигналов в разработке')" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
            <span class="text-[10px] font-medium">Сигналы</span>
        </button>
        <button onclick="alert('Настройки аккаунта Клуба')" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.08 1.97.53 2.572 1.065z"></path></svg>
            <span class="text-[10px] font-medium">Настройки</span>
        </button>
    </div>

    <script>
        let currentPair = 'EURGBP';

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
            ['eurgbp', 'btcusd', 'xauusd'].forEach(p => {
                const btn = document.getElementById(`btn-${p}`);
                if (p === pair.toLowerCase()) {
                    btn.className = "py-2.5 px-3 rounded-xl active-tab text-cyan-300 font-bold text-xs transition active:scale-95 flex flex-col items-center";
                } else {
                    btn.className = "py-2.5 px-3 rounded-xl glass-card text-gray-400 font-medium text-xs transition active:scale-95 flex flex-col items-center";
                }
            });
            document.getElementById('pair-title').innerText = pair;
            fetchData();
        }

        async function fetchData() {
            try {
                const res = await fetch(`/api/data/${currentPair}`);
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
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 glow-buy";
                    vText.style.color = '#00ff88';
                    badgeTrend.innerText = 'БЫЧИЙ ТРЕНД';
                    badgeTrend.className = "px-2.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold";
                } else if (data.synergy.action === 'SELL') {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 glow-sell";
                    vText.style.color = '#ff3b30';
                    badgeTrend.innerText = 'МЕДВЕЖИЙ ТРЕНД';
                    badgeTrend.className = "px-2.5 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold";
                } else {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300";
                    vText.style.color = '#ffd700';
                    badgeTrend.innerText = 'ОЖИДАНИЕ';
                    badgeTrend.className = "px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold";
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
