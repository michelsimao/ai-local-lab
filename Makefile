VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
UVICORN=$(VENV)/bin/uvicorn

.PHONY: install run ui test integration clean

install:
	python3 -m venv $(VENV)
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ui:
	streamlit run ui/streamlit_app.py

test:
	$(PYTHON) -m pytest -q

integration:
	export OLLAMA_BASE_URL=http://127.0.0.1:11434 && $(PYTHON) -m pytest tests/integration -q

clean:
	rm -rf $(VENV)
