.PHONY: backend frontend test sample-data docker-up

backend:
	cd backend && source venv/bin/activate 2>/dev/null || true; uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && source venv/bin/activate && cd .. && pytest tests/ -v

sample-data:
	python3 scripts/generate_sample_data.py

docker-up:
	docker compose up --build
