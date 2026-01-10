# Makefile
SHELL := /usr/bin/env bash

ROOT_DIR := $(shell pwd)
BACKEND_DIR ?= $(ROOT_DIR)
BACKEND_PORT ?= 8000
DOCS_PORT ?= 8001
ENV_FILE ?= $(BACKEND_DIR)/.env

.PHONY: help install api web build-web serve-web android qr kill-ports ip docs docs-build

help:
	@echo "Targets:"
	@echo "  make install     - uv sync (backend) + spaCy models"
	@echo "  make api         - avvia FastAPI (uvicorn) su 0.0.0.0:$(BACKEND_PORT)"
	@echo "  make docs        - serve documentation on http://localhost:$(DOCS_PORT)"
	@echo "  make docs-build  - build static documentation site"

install:
	./run.sh install
	@echo "📦 Installing spaCy Italian model..."
	uv run python -m spacy download it_core_news_lg

api:
	./run.sh run-api

serve:
	uv run mkdocs serve

docs:
	@echo "📚 Serving documentation on http://localhost:$(DOCS_PORT)"
	@echo "   Press Ctrl+C to stop"
	uv run mkdocs serve -a localhost:$(DOCS_PORT)

docs-build:
	@echo "🏗️  Building static documentation..."
	uv run mkdocs build
	@echo "✅ Documentation built in site/"
