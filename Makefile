.PHONY: install test benchmark-smoke install-heavy check-backends ablation-smoke

install:
	python -m pip install -e .

test:
	pytest -q

benchmark-smoke:
	python benchmarks/run_benchmark.py --config benchmarks/configs/synthetic_smoke.yaml --output results/synthetic_smoke

ablation-smoke:
	python experiments/run_ablation.py --config experiments/ablation_configs/mock_smoke.yaml --output results/mock_ablation

check-backends:
	python -m app.backends.check

install-heavy:
	python -m pip install -e ".[heavy]"
