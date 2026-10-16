install:
	python -m pip install -e . pytest kaggle
test:
	pytest -q
synthetic:
	python scripts/make_synthetic_data.py
	python -m bosch_pipeline.prepare --config configs.synthetic.yaml
	python -m bosch_pipeline.train --config configs.synthetic.yaml
prepare:
	python -m bosch_pipeline.prepare --config configs.yaml
train:
	python -m bosch_pipeline.train --config configs.yaml
