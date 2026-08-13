.PHONY: setup generate-data test run-local run-ui evaluate-accuracy evaluate-determinism report init-db capture-env

setup:
	uv python install 3.12
	uv sync --python 3.12
	cp -n .env.example .env || true

generate-data:
	uv run python scripts/generate_cases.py

init-db:
	uv run python scripts/initialize_database.py

test:
	uv run pytest -q

run-local:
	uv run python scripts/run_case.py --case case_001 --mode evaluate

run-ui:
	uv run streamlit run app/ui.py

evaluate-accuracy:
	uv run python scripts/evaluate_accuracy.py

evaluate-determinism:
	uv run python scripts/evaluate_determinism.py

capture-env:
	uv run python scripts/capture_environment.py

report: capture-env
	uv run python scripts/build_report.py
