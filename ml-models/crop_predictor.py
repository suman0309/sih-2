import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    from lightgbm import LGBMRegressor  # type: ignore
    _HAS_LGBM = True
except Exception:  # pragma: no cover - optional dependency
    LGBMRegressor = None  # type: ignore
    _HAS_LGBM = False

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import joblib


@dataclass
class TrainedCropModel:
    model_name: str
    model: object
    feature_columns: List[str]
    target_name: str
    residual_std: float
    training_rows: int


class CropYieldPredictor:
    """
    Hybrid, per-crop regression ensemble with confidence intervals and rule-based risk factors.

    Expected input schema:
    - weather_data: DataFrame with columns like ['temperature', 'rainfall', 'humidity', 'radiation', 'wind_speed']
    - soil_data: DataFrame with columns like ['ph', 'nitrogen', 'phosphorus', 'potassium', 'organic_matter', 'soil_moisture']
    - yield_data: DataFrame with columns ['crop', 'yield'] aligned by index or including an 'id' to merge on
    The `feature_engineering` method aligns indices; if an 'id' column exists in all inputs, it uses it to merge.

    Prediction input schema:
    - DataFrame containing the same feature columns used during training plus a 'crop' column.
    """

    def __init__(self, target_name: str = "yield") -> None:
        self.target_name = target_name
        self.models: Dict[str, TrainedCropModel] = {}

    # ----------------------------- Public API ----------------------------- #
    def train_hybrid_model(
        self,
        weather_data: pd.DataFrame,
        soil_data: pd.DataFrame,
        yield_data: pd.DataFrame,
    ) -> Dict[str, TrainedCropModel]:
        """Train per-crop models and store internal state.

        The method builds features, merges target, splits by crop, and trains a model per crop.
        LGBM is preferred if available; otherwise RandomForest is used.
        """
        features = self.feature_engineering(weather_data, soil_data)

        # Merge target
        target_df = self._align_target(features, yield_data)
        data = features.join(target_df[["crop", self.target_name]])

        # Guard
        if "crop" not in data.columns:
            raise ValueError("'crop' column is required in yield_data for per-crop training")

        # Train per crop
        models: Dict[str, TrainedCropModel] = {}
        for crop_name, crop_df in data.groupby("crop"):
            X = crop_df.drop(columns=["crop", self.target_name])
            y = crop_df[self.target_name]

            if len(X) < 10:
                # Too little data to train a stable model
                continue

            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = self._build_crop_model(crop_name)
            model.fit(X_train, y_train)

            # Residual std estimated on validation
            y_pred_val = model.predict(X_val)
            rmse = mean_squared_error(y_val, y_pred_val, squared=False)

            models[crop_name] = TrainedCropModel(
                model_name=type(model).__name__,
                model=model,
                feature_columns=list(X.columns),
                target_name=self.target_name,
                residual_std=float(rmse),
                training_rows=int(len(X)),
            )

        if not models:
            raise ValueError("No crop models were trained; provide more data.")

        self.models = models
        return models

    def predict_with_confidence(
        self, input_data: pd.DataFrame
    ) -> Union[Dict[str, Union[float, List[str], Tuple[float, float]]], List[Dict[str, Union[str, float, List[str], Tuple[float, float]]]]]:
        """Predict yields with confidence intervals and risk factors.

        If a single row is provided, returns a single dict. Otherwise returns a list of dicts.
        """
        if input_data.empty:
            return []

        if "crop" not in input_data.columns:
            raise ValueError("Input must include a 'crop' column for per-crop prediction")

        # Build features using input_data for both weather and soil placeholders.
        # feature_engineering will select intersecting columns.
        features = self.feature_engineering(input_data, input_data)

        results: List[Dict[str, Union[str, float, List[str], Tuple[float, float]]]] = []
        for idx, row in input_data.iterrows():
            crop_name = str(row["crop"]).lower()
            if crop_name not in self.models:
                results.append({
                    "crop": crop_name,
                    "yield": float("nan"),
                    "confidence_score": 0.0,
                    "interval": (float("nan"), float("nan")),
                    "risk_factors": ["unseen_crop_model"]
                })
                continue

            trained = self.models[crop_name]
            # Align feature columns
            X_row = self._safe_feature_row(features.loc[[idx]], trained.feature_columns)
            pred = float(trained.model.predict(X_row)[0])

            low, high, score = self._confidence_interval(pred, trained.residual_std)
            risks = self.identify_risks(row.to_dict())

            results.append({
                "crop": crop_name,
                "yield": pred,
                "confidence_score": score,
                "interval": (low, high),
                "risk_factors": risks,
            })

        if len(results) == 1:
            single = results[0].copy()
            single.pop("crop", None)
            return single
        return results

    # --------------------------- Helper methods -------------------------- #
    def feature_engineering(
        self, weather_data: pd.DataFrame, soil_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Create numeric features by aligning indices and computing aggregates.

        - If an 'id' column exists in both frames, merge on 'id'. Otherwise aligns by index.
        - Selects numeric columns only, with safe fillna.
        - Adds simple interaction features.
        """
        w = weather_data.copy()
        s = soil_data.copy()

        key_col = None
        if "id" in w.columns and "id" in s.columns:
            key_col = "id"
            w = w.set_index("id")
            s = s.set_index("id")

        # Align indexes
        if not w.index.equals(s.index):
            common_index = w.index.intersection(s.index)
            w = w.loc[common_index]
            s = s.loc[common_index]

        # Numeric selection
        w_num = w.select_dtypes(include=[np.number])
        s_num = s.select_dtypes(include=[np.number])

        # Basic cleaning
        w_num = w_num.replace([np.inf, -np.inf], np.nan).fillna(w_num.median(numeric_only=True))
        s_num = s_num.replace([np.inf, -np.inf], np.nan).fillna(s_num.median(numeric_only=True))

        # Rename columns to avoid collisions
        w_num = w_num.add_prefix("w_")
        s_num = s_num.add_prefix("s_")

        features = pd.concat([w_num, s_num], axis=1)

        # Simple interactions if columns are present
        if "w_rainfall" in features.columns and "s_soil_moisture" in features.columns:
            features["int_rainfall_soil_moisture"] = (
                features["w_rainfall"].astype(float) * features["s_soil_moisture"].astype(float)
            )
        if "w_temperature" in features.columns and "s_organic_matter" in features.columns:
            features["int_temp_organic"] = (
                features["w_temperature"].astype(float) * features["s_organic_matter"].astype(float)
            )

        # Optionally restore id as column (not needed for model)
        if key_col is not None:
            features.index.name = key_col

        return features

    def identify_risks(self, input_row: Dict[str, Union[str, float, int]]) -> List[str]:
        """Rule-based risk identification based on common agronomic thresholds.

        Uses whatever keys are present; safe lookups with defaults.
        """
        risks: List[str] = []

        def _get(name: str, default: float) -> float:
            try:
                val = input_row.get(name, default)
                return float(val)  # type: ignore
            except Exception:
                return default

        # Weather risks
        rainfall = _get("rainfall", _get("w_rainfall", 0.0))
        temperature = _get("temperature", _get("w_temperature", 0.0))
        humidity = _get("humidity", _get("w_humidity", 50.0))

        # Soil risks
        soil_moisture = _get("soil_moisture", _get("s_soil_moisture", 0.0))
        nitrogen = _get("nitrogen", _get("s_nitrogen", 0.0))
        phosphorus = _get("phosphorus", _get("s_phosphorus", 0.0))
        potassium = _get("potassium", _get("s_potassium", 0.0))
        ph = _get("ph", _get("s_ph", 7.0))

        if rainfall < 50:
            risks.append("low_rainfall")
        if temperature > 35:
            risks.append("heat_stress")
        if humidity < 30:
            risks.append("low_humidity")
        if soil_moisture < 20:
            risks.append("dry_soil")
        if nitrogen < 20:
            risks.append("nitrogen_deficit")
        if phosphorus < 15:
            risks.append("phosphorus_deficit")
        if potassium < 15:
            risks.append("potassium_deficit")
        if ph < 5.5 or ph > 8.0:
            risks.append("unfavorable_ph")

        return risks

    # ---------------------------- Internal utils ------------------------- #
    def _align_target(self, features: pd.DataFrame, yield_data: pd.DataFrame) -> pd.DataFrame:
        if "id" in yield_data.columns and features.index.name == "id":
            yd = yield_data.set_index("id")
            yd = yd.loc[features.index.intersection(yd.index)]
        else:
            # Assume aligned by index
            yd = yield_data.copy()
            if not features.index.equals(yd.index):
                common_index = features.index.intersection(yd.index)
                yd = yd.loc[common_index]
                # also reduce features to match
                _ = features.loc[common_index]
        # Normalize crop name to lowercase for grouping consistency
        if "crop" in yd.columns:
            yd["crop"] = yd["crop"].astype(str).str.lower()
        return yd

    def _build_crop_model(self, crop_name: str):
        crop_name = crop_name.lower()
        # Example specialization: use different estimators per crop
        if _HAS_LGBM and crop_name in {"rice", "sugarcane"}:
            return LGBMRegressor(n_estimators=500, random_state=42)
        if crop_name == "wheat":
            return RandomForestRegressor(n_estimators=300, random_state=42)
        # Fallback
        if _HAS_LGBM:
            return LGBMRegressor(n_estimators=300, random_state=42)
        return RandomForestRegressor(n_estimators=300, random_state=42)

    def _safe_feature_row(self, row_features: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        X = pd.DataFrame(columns=cols, index=row_features.index)
        for c in cols:
            if c in row_features.columns:
                X[c] = row_features[c]
            else:
                X[c] = 0.0
        return X.astype(float)

    def _confidence_interval(self, pred: float, residual_std: float, z: float = 1.96) -> Tuple[float, float, float]:
        # Basic normal-theory interval using validation RMSE as sigma
        interval_radius = z * float(max(residual_std, 1e-6))
        low = float(pred - interval_radius)
        high = float(pred + interval_radius)
        # Confidence score inversely proportional to relative width
        denom = abs(pred) + 1e-6
        relative_width = (high - low) / denom
        score = float(max(0.0, min(1.0, 1.0 / (1.0 + relative_width))))
        return low, high, score

    # --------------------------- Persistence API ------------------------- #
    def save(self, path: str) -> None:
        """Persist trained models and metadata to disk using joblib."""
        state = {
            "target_name": self.target_name,
            "models": {
                crop: {
                    "model_name": m.model_name,
                    "feature_columns": m.feature_columns,
                    "target_name": m.target_name,
                    "residual_std": m.residual_std,
                    "training_rows": m.training_rows,
                }
                for crop, m in self.models.items()
            },
        }
        # Save estimators separately to keep file size manageable and avoid pickling issues
        payload = {"state": state, "estimators": {}}
        for crop, m in self.models.items():
            payload["estimators"][crop] = m.model
        joblib.dump(payload, path)

    @classmethod
    def load(cls, path: str) -> "CropYieldPredictor":
        """Load a previously saved predictor from disk."""
        payload = joblib.load(path)
        state = payload["state"]
        estimators = payload["estimators"]

        obj = cls(target_name=state.get("target_name", "yield"))
        models: Dict[str, TrainedCropModel] = {}
        for crop, meta in state["models"].items():
            models[crop] = TrainedCropModel(
                model_name=meta["model_name"],
                model=estimators[crop],
                feature_columns=list(meta["feature_columns"]),
                target_name=meta["target_name"],
                residual_std=float(meta["residual_std"]),
                training_rows=int(meta["training_rows"]),
            )
        obj.models = models
        return obj


