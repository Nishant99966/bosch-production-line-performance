#!/usr/bin/env bash
set -euo pipefail
python -m bosch_pipeline.prepare --config configs.yaml
python -m bosch_pipeline.train --config configs.yaml
