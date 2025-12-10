# Makefile
SHELL := /usr/bin/env bash

ROOT_DIR := $(shell pwd)
BACKEND_DIR ?= $(ROOT_DIR)/backend
BACKEND_PORT ?= 8000
ENV_FILE ?= $(BACKEND_DIR)/.env

.PHONY: help install api web build-web serve-web android qr kill-ports ip

help:
	@echo "Targets:"
	@echo "  make install     - uv sync (backend)"
	@echo "  make api         - avvia FastAPI (uvicorn) su 0.0.0.0:$(BACKEND_PORT)"

install:
	cd "$(BACKEND_DIR)" && uv sync

api:
	cd "$(BACKEND_DIR)" && uv run uvicorn app.main:app --host 0.0.0.0 --port "$(BACKEND_PORT)" --env-file "$(ENV_FILE)" --reload