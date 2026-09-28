.PHONY: setup test generate run eval eval-holdout ui commercial

setup:
	uv sync

test:
	uv run pytest -q

# Regenerate every synthetic deal package from data/specs/*.yaml.
generate:
	uv run python scripts/qoe_generate_deals.py --all

run:
	uv run python scripts/qoe_run.py --deal data/dev/meridian_mechanical --xlsx

eval:
	uv run python scripts/qoe_evaluate.py --split dev

# Run only after development is frozen; see docs/benchmark_protocol.md.
eval-holdout:
	uv run python scripts/qoe_evaluate.py --split holdout

ui:
	uv run streamlit run qoe/ui.py

commercial:
	uv run python scripts/qoe_commercial_model.py
