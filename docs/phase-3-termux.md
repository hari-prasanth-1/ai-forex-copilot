# Phase 3A — Termux mobile mode

Android → Termux → FastAPI/PWA → read-only market data → analysis/risk engine

This phase does not connect to the MT5 Android application and does not place orders.
The MT5 desktop Python bridge remains a later phase and requires a desktop terminal.

## Setup

Install Termux from its official distribution, then:

    pkg update
    pkg install python git
    python -m pip install --upgrade pip
    git clone https://github.com/hari-prasanth-1/ai-forex-copilot.git
    cd ai-forex-copilot
    git checkout develop
    python -m pip install -r requirements.txt

Run:

    python -m uvicorn api.app:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000 on the phone.

For a direct mobile-data check:

    python -c "from api.mobile_market import build_mobile_analysis; print(build_mobile_analysis('AUDUSD','M15'))"

AUDUSD is mapped to Yahoo's AUDUSD=X symbol for development analysis only.

Never commit broker passwords or API keys. Do not expose Uvicorn directly to the public internet.
