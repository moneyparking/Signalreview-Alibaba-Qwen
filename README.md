# SignalReview Alibaba Qwen Hackathon API

Isolated FastAPI demo for Alibaba Cloud Qwen agent orchestration.

Repository: moneyparking/Signalreview-Alibaba-Qwen

Core files:

- live_match_processor.py
- live_routes.py
- main.py
- deploy.sh
- requirements.txt
- .env.example

Run locally:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Deploy on Alibaba ECS:

export DASHSCOPE_API_KEY='your_key'
export QWEN_MODEL='qwen2.5-72b-instruct'
git clone https://github.com/moneyparking/Signalreview-Alibaba-Qwen.git
cd Signalreview-Alibaba-Qwen
sudo -E bash deploy.sh

Health check:

curl http://127.0.0.1:8000/api/health

License: MIT
