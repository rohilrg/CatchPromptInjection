# Makefile for formatting and linting Python code using Black and Flake8

# Directories to process
SRC_DIR := ./src

# List of Python files to process
PYTHON_FILES := $(wildcard $(SRC_DIR)/*.py)

.PHONY: format lint

format:
	@echo "Formatting Python code using Black..."
	@black $(PYTHON_FILES)
	@black app.py

lint:
	@echo "Linting Python code using Flake8..."
	@flake8 $(PYTHON_FILES)  --ignore=E501,W503
	@flake8 app.py --ignore=E501,W503

test:
	@echo "Linting Python code using Flake8..."
	@python -m pytest ./src/tests/test_detector.py