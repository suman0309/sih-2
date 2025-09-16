from pathlib import Path
import importlib.util


def _load_precision_engine():
    root = Path(__file__).resolve().parents[1]
    path = root / "ml-models" / "precision_agriculture.py"
    spec = importlib.util.spec_from_file_location("precision_agriculture", str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module.PrecisionAgricultureEngine


_ENGINE_CLS = _load_precision_engine()
_ENGINE_SINGLETON = None


class MLEngine:
    def generate_recommendations(self, field_data):
        # Mock recommendations for testing
        recommendations = [
            "Consider irrigation as soil moisture is below optimal level",
            "Apply nitrogen fertilizer in recommended doses",
            "Monitor temperature trends for heat stress",
        ]

        insight = {
            "risk_score": 0.3,
            "yield_prediction": 3.5,
            "confidence": 0.85,
        }

        return recommendations, insight


def get_engine():
    return MLEngine()



