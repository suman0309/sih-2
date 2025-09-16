import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


class WeatherService:
    def __init__(self, timeout_seconds: int = 10):
        self.imd_base_url = "https://mausam.imd.gov.in/api"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "CropIntel/1.0 (+https://example.org)"
        })

    def get_district_weather(self, district_code: str) -> Dict[str, Any]:
        """Integrate with IMD APIs for Odisha districts.

        Returns a processed dict with keys: current, forecast, rainfall, and derived fields.
        """
        endpoints = {
            "current": f"{self.imd_base_url}/current_wx_api.php?id={district_code}",
            "forecast": f"{self.imd_base_url}/cityweather.php?id={district_code}",
            "rainfall": f"{self.imd_base_url}/districtwise_rainfall_api.php",
        }

        raw: Dict[str, Any] = {}
        for key, url in endpoints.items():
            try:
                raw[key] = self._request_json(url)
            except Exception as exc:  # pragma: no cover - network variability
                raw[key] = {"error": str(exc), "_source_url": url}

        return self.process_weather_data(raw)

    def process_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize IMD responses to a consistent schema and compute derived metrics."""
        current = self._normalize_current(weather_data.get("current"))
        forecast = self._normalize_forecast(weather_data.get("forecast"))
        rainfall = self._normalize_rainfall(weather_data.get("rainfall"))

        # Compute simple derived metrics, e.g., next-3-day avg rainfall and heat flags
        next3_rain = sum([d.get("rainfall_mm", 0.0) for d in forecast[:3]]) if forecast else 0.0
        heatwave = any(d.get("max_temp_c", 0.0) >= 40.0 for d in forecast[:3]) if forecast else False

        return {
            "current": current,
            "forecast": forecast,
            "rainfall": rainfall,
            "derived": {
                "next3_day_rainfall_mm": round(float(next3_rain), 2),
                "heatwave_next3": bool(heatwave),
            },
        }

    def calculate_growing_degree_days(
        self,
        temp_data: List[Dict[str, Any]],
        crop: Optional[str] = None,
        base_temp_c: Optional[float] = None,
        upper_temp_c: Optional[float] = 30.0,
    ) -> float:
        """Calculate GDD for crop growth stages.

        temp_data: list of dicts with keys like {date, min_temp_c, max_temp_c} or {tmin, tmax}.
        crop: if provided, sets default base temperature by crop.
        base_temp_c: override base temperature if known; fallback uses crop-based defaults.
        upper_temp_c: cap for tmax when computing GDD (default 30C).
        """
        if base_temp_c is None:
            base_temp_c = self._crop_base_temp(crop)

        gdd_total = 0.0
        for d in temp_data:
            tmin = self._safe_get(d, ["min_temp_c", "tmin", "min"])
            tmax = self._safe_get(d, ["max_temp_c", "tmax", "max"])
            if tmin is None or tmax is None:
                # Try to derive from current object shape
                t = self._safe_get(d, ["temp_c", "temperature", "temp"])
                if t is None:
                    continue
                tmin = float(t)
                tmax = float(t)

            tmin = float(tmin)
            tmax = float(tmax)

            # Apply caps as per standard single-sine approximation shortcut
            tmax_capped = min(tmax, float(upper_temp_c) if upper_temp_c is not None else tmax)
            tmean = (tmax_capped + tmin) / 2.0
            gdd_day = max(0.0, tmean - float(base_temp_c))
            gdd_total += gdd_day

        return round(gdd_total, 2)

    # --------------------------- Internal helpers --------------------------- #
    def _request_json(self, url: str) -> Any:
        resp = self.session.get(url, timeout=self.timeout_seconds)
        resp.raise_for_status()
        # Some IMD endpoints may return text/plain JSON
        try:
            return resp.json()
        except ValueError:
            return json.loads(resp.text)

    def _normalize_current(self, payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {"raw": payload}
        # Try common shapes
        obj = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        out = {
            "observed_at": self._parse_dt(self._safe_get(obj, ["observation_time", "time", "obs_time"])),
            "temp_c": self._to_float(self._safe_get(obj, ["temp_c", "temperature", "temp"])) ,
            "humidity": self._to_float(self._safe_get(obj, ["humidity", "rh"])) ,
            "wind_kph": self._to_float(self._safe_get(obj, ["wind_speed_kmph", "wind_kph", "wind"])) ,
            "rainfall_mm": self._to_float(self._safe_get(obj, ["rain_mm", "rainfall", "precip_mm"])) ,
        }
        return {k: v for k, v in out.items() if v is not None}

    def _normalize_forecast(self, payload: Any) -> List[Dict[str, Any]]:
        if payload is None:
            return []
        # Payload may be list or dict containing list
        items = []
        if isinstance(payload, list):
            items = payload
        elif isinstance(payload, dict):
            for key in ["forecast", "data", "DailyForecast", "list"]:
                val = payload.get(key)
                if isinstance(val, list):
                    items = val
                    break
        out: List[Dict[str, Any]] = []
        for it in items:
            out.append({
                "date": self._parse_dt(self._safe_get(it, ["date", "valid_date", "dt_txt", "day"])),
                "min_temp_c": self._to_float(self._safe_get(it, ["mintemp_c", "tmin", "min_temp_c", "min"])),
                "max_temp_c": self._to_float(self._safe_get(it, ["maxtemp_c", "tmax", "max_temp_c", "max"])),
                "rainfall_mm": self._to_float(self._safe_get(it, ["rain_mm", "rainfall", "precip_mm", "rain"])),
                "condition": self._safe_get(it, ["condition", "weather", "summary"]) ,
            })
        # filter Nones-only dicts
        cleaned = []
        for row in out:
            if any(v is not None for v in row.values()):
                cleaned.append(row)
        return cleaned

    def _normalize_rainfall(self, payload: Any) -> List[Dict[str, Any]]:
        if payload is None:
            return []
        # IMD districtwise_rainfall_api might return per-district entries
        items = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
        out: List[Dict[str, Any]] = []
        for it in items:
            out.append({
                "district": self._safe_get(it, ["district", "name"]),
                "rainfall_mm": self._to_float(self._safe_get(it, ["rainfall", "rain_mm", "mm"])) ,
                "date": self._parse_dt(self._safe_get(it, ["date", "dt", "day"])) ,
            })
        return out

    def _crop_base_temp(self, crop: Optional[str]) -> float:
        if not crop:
            return 10.0
        name = crop.strip().lower()
        defaults = {
            "wheat": 4.0,
            "rice": 10.0,
            "maize": 8.0,
            "sugarcane": 12.0,
            "cotton": 15.0,
            "soybean": 10.0,
            "potato": 7.0,
        }
        return float(defaults.get(name, 10.0))

    def _safe_get(self, obj: Any, keys: List[str]) -> Optional[Any]:
        if not isinstance(obj, dict):
            return None
        for k in keys:
            if k in obj and obj[k] not in ("", None):
                return obj[k]
        return None

    def _to_float(self, val: Optional[Any]) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except Exception:
            return None

    def _parse_dt(self, val: Optional[Any]) -> Optional[str]:
        if not val:
            return None
        if isinstance(val, (int, float)):
            try:
                # Assume unix seconds
                return datetime.utcfromtimestamp(float(val)).isoformat()
            except Exception:
                return None
        if isinstance(val, str):
            # Try common IMD/ISO formats
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"):
                try:
                    return datetime.strptime(val, fmt).isoformat()
                except Exception:
                    continue
            try:
                # Last resort: if already ISO-like
                return datetime.fromisoformat(val.replace("Z", "+00:00")).isoformat()
            except Exception:
                return None
        return None


