import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent

def _load_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module

PrecisionAgriculture = _load_module_from_path(
    "precision_agriculture", ROOT / "ml-models" / "precision_agriculture.py"
)
Blockchain = _load_module_from_path(
    "blockchain_service", ROOT / "backend" / "blockchain_service.py"
)


def main():
    engine = PrecisionAgriculture.PrecisionAgricultureEngine()
    recs, insight = engine.generate_recommendations({
        "crop": "rice",
        "soil_moisture": 18,
        "rainfall_mm": 2,
        "temperature": 34,
        "days_after_sowing": 70,
        "month": 7,
        "nitrogen": 15,
        "phosphorus": 12,
        "potassium": 14,
    })

    print("Recommendations:")
    print(recs)
    print("\nInsight:")
    print(insight)

    bc = Blockchain.AgriBlockchain()
    h = bc.add_prediction_record("farmer123", {"crop": "rice"}, {"yield": 3.4})
    result = bc.verify_prediction_accuracy(h, actual_yield=3.2)
    print("\nBlockchain verification:")
    print(result)


if __name__ == "__main__":
    main()


