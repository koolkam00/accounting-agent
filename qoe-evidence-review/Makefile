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

# The reviewer app has no authentication and shows confidential deal data, so it binds
# to this machine only (http://127.0.0.1:8501). To reach it from elsewhere, put an
# authenticating proxy in front; do not rebind it to 0.0.0.0. Held-out packages stay
# hidden unless QOE_SHOW_HOLDOUT=1 (benchmark sessions only).
ui:
	uv run streamlit run qoe/ui.py --server.address 127.0.0.1

commercial:
	uv run python scripts/qoe_commercial_model.py
