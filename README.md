# Omnipredict_IDE

I built Omnipredict as the web platform for the OMNIPREDICT project, whose full name is *Omics and Non-invasive Integration for Predictive Health Assessment*. The goal of the project is the early detection of sarcopenia through the integration of clinical, functional, biochemical, and genomic data. The platform is deployed at [omnipredict.it](https://omnipredict.it/).

## Links

- Live platform: [https://omnipredict.it/](https://omnipredict.it/)
- Funding context: [AGE-IT Spoke 3 cascade call for enterprises](https://ageit.eu/wp/2024/08/07/spoke-3-pubblicato-il-secondo-bando-a-cascata-rivolto-alle-imprese/)
- Public signup/login demo: anyone can create an account on the live website and explore the platform workflow directly.

## Project Context

I built Omnipredict around a sarcopenia use case targeting older patients with multimorbidity. The project combines:

- body-composition measurements,
- functional indicators such as hand-grip strength,
- lipidomic profiling,
- selected SNPs,
- protein markers such as BAG3 and Sortilin.

The web application is the platform layer that hosts the predictive workflow and exposes it through a usable interface.

## Modelling Approach

The project started from the idea of an advanced AI classifier for early sarcopenia detection. During the pilot work I revised the modelling strategy and moved away from deep learning for the core classifier, because the available tabular dataset was too small for a neural-network-first approach to generalize reliably.

The current repository reflects that decision:

- I prepared a full preprocessing pipeline,
- engineered clinically meaningful features,
- evaluated multiple tree-based models,
- selected XGBoost as the primary direction,
- kept LightGBM and other baselines for comparison.

## What The Repository Contains

This repository contains the deployed Django platform around the classifier workflow:

- account management,
- manual and file-based prediction flows,
- saved prediction history,
- deployment configuration for the hosted platform.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

## Notes

- The trained model artifacts are not distributed in this public repository because they are proprietary.
- The raw project dataset is also omitted from the public repository because it contains sensitive project data.
- If you want to run predictions locally, you need to provide the proprietary files expected under `models/`.
- This repository is the web-facing part of the project: the training notebooks and technical reports document the modelling work in more detail, while this codebase focuses on deployment and usage.
