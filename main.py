from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
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

def normalize_key(pair_str: str) -> str:
    clean = pair_str.upper().replace("/", "").replace("=X", "").strip()
    if len(clean) == 6:
        return f"{clean[:3]}/{clean[3:]}"
    return clean

@app.post("/api/webhook")
async def receive_webhook(payload: EmeraldPayload):
    try:
        norm_key = normalize_key(payload.pair)
        data = payload.dict()
        data["pair"] = norm_key
        storage[norm_key] = data
        print(f"✅ Данные приняты для {norm_key} | Цена: {data['price']}")
        return {"status": "success", "pair": norm_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/data/{pair:path}")
async def get_pair_data(pair: str):
    norm_key = normalize_key(pair)
    for key in storage:
        if normalize_key(key) == norm_key:
            return storage[key]
            
    return {
        "pair": norm_key,
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
                    <p class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">FOREX TERMINAL</p>
                </div>
            </div>
            <div class="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold flex items-center gap-1.5 shadow-sm shadow-emerald-500/10">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> Клуб
            </div>
        </div>

        <!-- Сетка выбора Forex пар (2 ряда по 3 пары — всё видно на экране без скролла) -->
        <div id="pairs-container" class="grid grid-cols-3 gap-2 mb-5"></div>

        <div id="tab-terminal" class="space-y-4">
            <div id="main-card" class="glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden">
                <div class="absolute -right-10 -top-10 w-32 h-32 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none"></div>

                <div class="flex justify-between items-center mb-2">
                    <span class="text-[11px] font-bold tracking-wider text-gray-400 flex items-center gap-1.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-400"></span> ПРЯМО СЕЙЧАС
                    </span>
                    <span id="badge-trend" class="px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/40 text-emerald-400 text-xs font-extrabold tracking-wide flex items-center gap-1">
                        ОЖИДАНИЕ
                    </span>
                </div>

                <div class="mb-4">
                    <h2 id="pair-title" class="text-2xl font-black text-white tracking-tight">EUR/GBP</h2>
                    <div class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-teal-300 to-emerald-300 mt-1 flex items-baseline gap-2">
                        <span id="price-val">0.00000</span>
                    </div>
                </div>

                <div class="bg-gray-950/70 p-4 rounded-xl border border-gray-800/80 shadow-inner">
                    <div class="text-[10px] font-extrabold uppercase tracking-widest text-gray-400 mb-1">Вердикт алгоритма</div>
                    <div id="v-text" class="text-lg font-black text-amber-400 tracking-wide">NEUTRAL WAIT</div>
                    
                    <div class="flex justify-between items-center mt-3 text-xs text-gray-400 font-medium">
                        <span>До зоны входа</span>
                        <span id="m-dist" class="font-bold text-white">0.05%</span>
                    </div>
                    <div class="w-full bg-gray-900 h-2.5 rounded-full mt-2 overflow-hidden p-0.5 border border-gray-800">
                        <div id="progress-bar" class="bg-gradient-to-r from-cyan-400 via-teal-400 to-emerald-400 h-full w-3/4 rounded-full transition-all duration-500 shadow-sm shadow-emerald-400/50"></div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Индекс Херста</div>
                    <div id="m-hurst" class="text-xl font-black text-white">0.50</div>
                    <div class="text-[10px] font-semibold text-cyan-400 mt-0.5">Трендовый режим</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Information Ratio</div>
                    <div id="m-ir" class="text-xl font-black text-emerald-400">0.00</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Эффективность</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Модель Сорнетте</div>
                    <div id="m-lppl" class="text-base font-black text-emerald-400">WAIT</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Риск пузыря</div>
                </div>
                <div class="glass-card p-4 rounded-2xl relative overflow-hidden">
                    <div class="text-[10px] uppercase font-bold text-gray-400 mb-1">Синергия сети</div>
                    <div id="v-score" class="text-xl font-black text-amber-400">50/100</div>
                    <div class="text-[10px] font-semibold text-gray-400 mt-0.5">Точность</div>
                </div>
            </div>
        </div>

        <div id="tab-sessions" class="space-y-4 hidden">
            <div class="glass-card rounded-2xl p-4">
                <h3 class="text-sm font-extrabold text-white mb-1">Сессии и ICT Killzones</h3>
                <p class="text-[11px] text-gray-400 mb-4 font-medium">Время мировых бирж · UTC</p>
                <div class="space-y-2.5">
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400"></span> Сидней</span>
                        <span class="text-xs font-extrabold text-emerald-400">АКТИВНО</span>
                    </div>
                    <div class="flex justify-between items-center bg-gray-950/60 p-3 rounded-xl border border-gray-800">
                        <span class="text-xs font-bold text-white flex items-center gap-2"><span class="w-2 h-2 rounded-full bg-emerald-400"></span> Токио</span>
                        <span class="text-xs font-extrabold text-emerald-400">АКТИВНО</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="fixed bottom-0 left-0 right-0 max-w-md mx-auto bg-[#070b0f]/95 backdrop-blur-2xl border-t border-gray-800/80 px-6 py-3 flex justify-between items-center z-50">
        <button onclick="switchTab('terminal')" id="nav-terminal" class="flex flex-col items-center gap-1 text-cyan-400 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            <span class="text-[10px] font-bold">Терминал</span>
        </button>
        <button onclick="switchTab('sessions')" id="nav-sessions" class="flex flex-col items-center gap-1 text-gray-500 hover:text-gray-300 transition">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span class="text-[10px] font-semibold">Сессии</span>
        </button>
    </div>

    <script>
        const pairsList = ['EUR/GBP', 'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD'];
        let currentPair = 'EUR/GBP';

        function renderPairs() {
            const container = document.getElementById('pairs-container');
            container.innerHTML = '';
            pairsList.forEach(p => {
                const btn = document.createElement('button');
                btn.onclick = () => changePair(p);
                btn.className = p === currentPair ? 
                    "py-2.5 px-1 rounded-xl active-tab text-cyan-300 font-extrabold text-xs transition active:scale-95 text-center flex items-center justify-center" :
                    "py-2.5 px-1 rounded-xl glass-card text-gray-400 font-semibold text-xs transition active:scale-95 text-center flex items-center justify-center";
                btn.innerText = p;
                container.appendChild(btn);
            });
        }

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
            renderPairs();
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
                } else if (data.synergy.action === 'SELL') {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden glow-sell";
                    vText.style.color = '#ff3b30';
                    badgeTrend.innerText = 'МЕДВЕЖИЙ ТРЕНД';
                } else {
                    card.className = "glass-card rounded-2xl p-5 transition-all duration-300 relative overflow-hidden";
                    vText.style.color = '#ffd700';
                    badgeTrend.innerText = 'ОЖИДАНИЕ';
                }
            } catch (e) {
                console.error(e);
            }
        }

        renderPairs();
        setInterval(fetchData, 10000);
        fetchData();
    </script>
</body>
</html>
    """
