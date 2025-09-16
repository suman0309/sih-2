from pathlib import Path
import importlib.util


def _load_predictor_cls():
    root = Path(__file__).resolve().parents[1]
    path = root / "ml-models" / "crop_predictor.py"
    spec = importlib.util.spec_from_file_location("crop_predictor", str(path))
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module.CropYieldPredictor


_PREDICTOR_CLS = _load_predictor_cls()
_SINGLETON = None


def get_predictor():
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = _PREDICTOR_CLS()
    return _SINGLETON


