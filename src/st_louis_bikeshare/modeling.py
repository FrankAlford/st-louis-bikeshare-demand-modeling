"""Modeling helpers that mirror the project notebooks.

The full training pipeline lives in the notebooks because it depends on large
external ridership, ACS, and tract-geometry inputs. This module keeps the core
estimator setup importable for smaller experiments and future refactoring.
"""

from __future__ import annotations

from sklearn.cross_decomposition import PLSRegression
from sklearn.ensemble import HistGradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import ElasticNet, RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def build_stacking_regressor(random_state: int = 42) -> StackingRegressor:
    """Build the stacked ensemble family used in the demand-modeling notebook.

    Hyperparameters here are conservative defaults for small experiments. The
    reported project results came from nested leave-one-city-out tuning in the
    source notebooks, not from this untuned factory alone.
    """

    estimators = [
        (
            "elastic_net",
            make_pipeline(
                StandardScaler(),
                ElasticNet(alpha=0.01, l1_ratio=0.7, max_iter=5_000, random_state=random_state),
            ),
        ),
        (
            "ridge",
            make_pipeline(StandardScaler(), RidgeCV(alphas=(0.1, 1.0, 10.0, 100.0))),
        ),
        (
            "hgb",
            HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, random_state=random_state),
        ),
        (
            "pls",
            make_pipeline(StandardScaler(), PLSRegression(n_components=5)),
        ),
    ]

    return StackingRegressor(
        estimators=estimators,
        final_estimator=ElasticNet(alpha=0.01, l1_ratio=0.1, max_iter=5_000, random_state=random_state),
        passthrough=False,
    )
