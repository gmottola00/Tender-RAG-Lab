# Makefile
SHELL := /usr/bin/env bash

ROOT_DIR := $(shell pwd)
BACKEND_DIR ?= $(ROOT_DIR)
BACKEND_PORT ?= 8000
ENV_FILE ?= $(BACKEND_DIR)/.venv

.PHONY: help install api web build-web serve-web android qr kill-ports ip

help:
	@echo "Targets:"
	@echo "  make install     - uv sync (backend)"
	@echo "  make api         - avvia FastAPI (uvicorn) su 0.0.0.0:$(BACKEND_PORT)"

install:
	./run.sh install

api:
	./run.sh run-api
