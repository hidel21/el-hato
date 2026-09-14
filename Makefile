# Atajos del proyecto. Tres comandos para tener todo corriendo:
#
#     docker compose up -d
#     make preparar
#     make correr

VENV  := backend/.venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
ALEMBIC := cd backend && ../$(VENV)/bin/alembic

.PHONY: preparar correr movil api web sembrar migrar reiniciar-base tests tests-web linter formato limpiar

IP := $(shell ip -4 -o addr show scope global 2>/dev/null | grep -v docker | grep -v br- | awk '{print $$4}' | cut -d/ -f1 | head -1)

## Instala todo y deja la base lista con la finca demo.
preparar:
	@test -f .env || cp .env.ejemplo .env
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -e "backend/[dev]"
	$(ALEMBIC) upgrade head
	cd backend && ../$(PY) scripts/seed.py
	cd frontend && npm install
	@echo ""
	@echo "Listo. Ahora: make correr"

## Levanta la API y el frontend juntos. Ctrl-C apaga los dos.
correr:
	@echo "API  http://localhost:8000/docs"
	@echo "Web  http://localhost:5173"
	@$(VENV)/bin/uvicorn --app-dir backend app.main:app --reload --port 8000 & \
	PID_API=$$!; \
	(cd frontend && npm run dev) & \
	PID_WEB=$$!; \
	trap 'kill $$PID_API $$PID_WEB 2>/dev/null' INT TERM EXIT; \
	wait

## Igual que correr, pero el frontend queda visible en la red local.
## La API NO se expone: el proxy de Vite la alcanza desde el propio servidor.
movil:
	@echo "En este equipo       http://localhost:5173"
	@echo "Desde el telefono    http://$(IP):5173   (misma red WiFi)"
	@echo ""
	@$(VENV)/bin/uvicorn --app-dir backend app.main:app --reload --port 8000 & \
	PID_API=$$!; \
	(cd frontend && npm run dev -- --host) & \
	PID_WEB=$$!; \
	trap 'kill $$PID_API $$PID_WEB 2>/dev/null' INT TERM EXIT; \
	wait

api:
	$(VENV)/bin/uvicorn --app-dir backend app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

sembrar:
	cd backend && ../$(PY) scripts/seed.py

migrar:
	$(ALEMBIC) upgrade head

## Borra el esquema y lo vuelve a crear con datos frescos.
reiniciar-base:
	$(ALEMBIC) downgrade base
	$(ALEMBIC) upgrade head
	cd backend && ../$(PY) scripts/seed.py

tests:
	cd backend && ../$(VENV)/bin/pytest -q

tests-web:
	cd frontend && npm test

linter:
	cd backend && ../$(VENV)/bin/ruff check . && ../$(VENV)/bin/ruff format --check .
	cd frontend && npm run lint

formato:
	cd backend && ../$(VENV)/bin/ruff format .
	cd frontend && npm run formato

limpiar:
	rm -rf $(VENV) frontend/node_modules frontend/dist
