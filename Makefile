.PHONY: setup generate-data generate-difficulty test run-local run-ui evaluate-accuracy evaluate-determinism report init-db capture-env

setup:
	uv python install 3.12
	uv sync --python 3.12
	cp -n .env.example .env || true

generate-data:
	uv run python scripts/generate_cases.py

generate-difficulty:
	uv run python scripts/generate_cases.py --difficulty all

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

# Live examples (require a running vLLM server; do not rent a GPU from make):
#   uv run python scripts/evaluate_accuracy.py --live --difficulty hard --temperature 0.7 --label grid
#   uv run python scripts/evaluate_determinism.py --live --difficulty easy --temperature 0 --reps 5 --conc 1 8 --label grid
#   uv run python scripts/evaluate_determinism.py --live --negative-control --difficulty easy --temperature 0 --label neg

capture-env:
	uv run python scripts/capture_environment.py

report: capture-env
	uv run python scripts/build_report.py
