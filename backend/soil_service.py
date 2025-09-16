import json
from typing import Any, Dict, List, Optional

import requests


class SoilIntelligence:
    def __init__(self, timeout_seconds: int = 10):
        self.soil_health_api = "https://soilhealth.dac.gov.in/api"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "CropIntel/1.0 (+https://example.org)",
        })

    def get_soil_recommendations(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate with Soil Health Card Portal data and produce recommendations."""
        soil_metrics = self.fetch_soil_data(location_data)

        ph_val = self._to_float(soil_metrics.get("ph"))
        recommendations = {
            "ph_adjustment": self.calculate_ph_needs(ph_val),
            "nutrient_plan": self.generate_nutrient_plan(soil_metrics),
            "organic_matter": self.assess_organic_content(soil_metrics),
            "irrigation_schedule": self.optimize_irrigation(soil_metrics),
            "source": soil_metrics.get("_source", "soil_health_card"),
        }

        return recommendations

    # ---------------------------- Integration ---------------------------- #
    def fetch_soil_data(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch soil metrics for a given location and normalize the schema.

        location_data can include keys like: state_code, district_code, block_code, village_code, pincode, lat, lon.
        This function attempts multiple endpoints if available.
        """
        # Placeholder endpoint patterns (actual SHC API docs may differ)
        endpoints = [
            f"{self.soil_health_api}/soilmetrics?pincode={location_data.get('pincode','')}",
            f"{self.soil_health_api}/soilmetrics?lat={location_data.get('lat','')}&lon={location_data.get('lon','')}",
        ]

        last_error: Optional[str] = None
        for url in endpoints:
            if url.endswith("=") or url.endswith("=&lon="):
                continue
            try:
                data = self._request_json(url)
                normalized = self._normalize_soil_payload(data)
                if normalized:
                    normalized["_source"] = url
                    return normalized
            except Exception as exc:  # pragma: no cover - network variability
                last_error = str(exc)

        # Fallback: return defaults if nothing fetched
        return {
            "ph": 7.0,
            "nitrogen": 40.0,
            "phosphorus": 20.0,
            "potassium": 20.0,
            "organic_matter": 1.5,
            "soil_moisture": 25.0,
            "_fallback_error": last_error,
        }

    # ------------------------- Recommendation logic ---------------------- #
    def calculate_ph_needs(self, ph_val: Optional[float]) -> Dict[str, Any]:
        target_low, target_high = 6.5, 7.5
        if ph_val is None:
            return {"status": "unknown", "advice": "Test soil pH to plan amendments."}
        if ph_val < target_low:
            delta = round(target_low - ph_val, 2)
            return {
                "status": "acidic",
                "delta": delta,
                "amendment": "agricultural_lime",
                "rate_hint_t_ha": round(1.5 * delta, 2),
            }
        if ph_val > target_high:
            delta = round(ph_val - target_high, 2)
            return {
                "status": "alkaline",
                "delta": delta,
                "amendment": "elemental_sulfur_or_gypsum",
                "rate_hint_t_ha": round(0.8 * delta, 2),
            }
        return {"status": "optimal"}

    def generate_nutrient_plan(self, soil_metrics: Dict[str, Any]) -> Dict[str, Any]:
        n = self._to_float(soil_metrics.get("nitrogen"))
        p = self._to_float(soil_metrics.get("phosphorus"))
        k = self._to_float(soil_metrics.get("potassium"))

        plan: Dict[str, Any] = {"status": "balanced", "recommendations": []}

        def add(name: str, advice: str, rate_kg_ha: float) -> None:
            plan["recommendations"].append({
                "nutrient": name,
                "advice": advice,
                "rate_kg_ha": round(rate_kg_ha, 1),
            })

        if n is None or n < 20:
            add("nitrogen", "Apply urea in split doses", 80.0)
            plan["status"] = "deficit"
        elif n < 40:
            add("nitrogen", "Apply moderate N with topdressing", 50.0)
            plan["status"] = "mild_deficit"

        if p is None or p < 15:
            add("phosphorus", "Apply DAP or SSP at sowing", 40.0)
            plan["status"] = "deficit"
        elif p < 25:
            add("phosphorus", "Moderate P basal application", 25.0)
            if plan["status"] == "balanced":
                plan["status"] = "mild_deficit"

        if k is None or k < 15:
            add("potassium", "Apply MOP; avoid leaching", 40.0)
            plan["status"] = "deficit"
        elif k < 25:
            add("potassium", "Apply K at early growth", 25.0)
            if plan["status"] == "balanced":
                plan["status"] = "mild_deficit"

        if not plan["recommendations"]:
            plan["recommendations"].append({
                "nutrient": "none",
                "advice": "Maintain balanced fertilization as per crop schedule",
                "rate_kg_ha": 0.0,
            })

        return plan

    def assess_organic_content(self, soil_metrics: Dict[str, Any]) -> Dict[str, Any]:
        om = self._to_float(soil_metrics.get("organic_matter"))
        if om is None:
            return {"status": "unknown", "advice": "Incorporate FYM/compost @ 5 t/ha"}
        if om < 1.0:
            return {"status": "low", "advice": "Apply compost/FYM @ 8-10 t/ha"}
        if om < 2.0:
            return {"status": "moderate", "advice": "Apply compost/FYM @ 5-6 t/ha"}
        return {"status": "good", "advice": "Maintain residues and green manures"}

    def optimize_irrigation(self, soil_metrics: Dict[str, Any]) -> Dict[str, Any]:
        sm = self._to_float(soil_metrics.get("soil_moisture"))
        rainfall = self._to_float(soil_metrics.get("rainfall_mm", 0.0))
        if sm is None:
            return {"status": "unknown", "schedule": "Irrigate per crop evapotranspiration"}
        if sm < 15:
            return {"status": "dry", "schedule": "Irrigate immediately; mulching recommended"}
        if sm < 25 and (rainfall is None or rainfall < 5):
            return {"status": "moderate", "schedule": "Irrigate within 2-3 days"}
        return {"status": "adequate", "schedule": "Monitor; no irrigation needed now"}

    # ------------------------------ Utils -------------------------------- #
    def _request_json(self, url: str) -> Any:
        resp = self.session.get(url, timeout=self.timeout_seconds)
        resp.raise_for_status()
        try:
            return resp.json()
        except ValueError:
            return json.loads(resp.text)

    def _to_float(self, val: Optional[Any]) -> Optional[float]:
        if val is None:
            return None
        try:
            return float(val)
        except Exception:
            return None


