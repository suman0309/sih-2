from typing import Any, Dict, Optional, Tuple


class PrecisionAgricultureEngine:
    def __init__(self, translator: Optional[Any] = None, terms: Optional[Dict[str, Dict[str, str]]] = None):
        self.crop_models = self.load_crop_specific_models()
        self.translator = translator
        self.terms = terms or {}

    def generate_recommendations(self, field_data: Dict[str, Any], language: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
        recommendations = {
            'irrigation': self.optimize_irrigation_schedule(field_data),
            'fertilization': self.calculate_nutrient_requirements(field_data),
            'planting': self.suggest_optimal_planting_dates(field_data),
            'harvest': self.predict_harvest_timing(field_data),
            'market_price': self.predict_market_prices(field_data),
            'risk_assessment': self.assess_climate_risks(field_data)
        }

        insights = self.generate_farmer_friendly_insights(recommendations, language)
        return recommendations, insights

    def optimize_irrigation_schedule(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        soil_moisture = float(field_data.get('soil_moisture', 25))
        rainfall_mm = float(field_data.get('rainfall_mm', 0))
        et0 = float(field_data.get('et0_mm', 4))
        crop = str(field_data.get('crop', 'rice')).lower()

        if soil_moisture < 15:
            schedule = 'Irrigate today (deficit)'
        elif soil_moisture < 25 and rainfall_mm < 5:
            schedule = 'Irrigate in 2 days'
        else:
            schedule = 'No irrigation needed today'

        return {
            'crop': crop,
            'status': 'deficit' if soil_moisture < 15 else 'moderate' if soil_moisture < 25 else 'adequate',
            'schedule': schedule,
            'et0_mm': et0,
        }

    def calculate_nutrient_requirements(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        n = float(field_data.get('nitrogen', 30))
        p = float(field_data.get('phosphorus', 20))
        k = float(field_data.get('potassium', 20))
        plan = []
        if n < 20:
            plan.append({'nutrient': 'N', 'rate_kg_ha': 80, 'advice': 'Apply urea in splits'})
        if p < 15:
            plan.append({'nutrient': 'P', 'rate_kg_ha': 40, 'advice': 'Apply DAP/SSP as basal'})
        if k < 15:
            plan.append({'nutrient': 'K', 'rate_kg_ha': 40, 'advice': 'Apply MOP early'})
        if not plan:
            plan.append({'nutrient': 'balanced', 'rate_kg_ha': 0, 'advice': 'Maintain current schedule'})
        return {'status': 'deficit' if len(plan) > 1 else 'balanced', 'recommendations': plan}

    def suggest_optimal_planting_dates(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        crop = str(field_data.get('crop', 'rice')).lower()
        month = int(field_data.get('month', 7))
        if crop == 'rice':
            window = 'June-July'
        elif crop == 'wheat':
            window = 'November'
        else:
            window = 'Seasonal window varies'
        return {'crop': crop, 'recommended_window': window, 'current_month': month}

    def predict_harvest_timing(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        crop = str(field_data.get('crop', 'rice')).lower()
        days_after_sowing = int(field_data.get('days_after_sowing', 60))
        typical_duration = 120 if crop == 'rice' else 140 if crop == 'wheat' else 100
        remaining = max(0, typical_duration - days_after_sowing)
        return {'crop': crop, 'remaining_days': remaining, 'typical_duration_days': typical_duration}

    def predict_market_prices(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        crop = str(field_data.get('crop', 'rice')).lower()
        base_price = 2000 if crop == 'rice' else 2200 if crop == 'wheat' else 1800
        trend = 'stable'
        return {'crop': crop, 'msp_like_price_inr_qtl': base_price, 'trend': trend}

    def assess_climate_risks(self, field_data: Dict[str, Any]) -> Dict[str, Any]:
        rainfall = float(field_data.get('rainfall_mm', 0))
        temp = float(field_data.get('temperature', 30))
        risks = []
        if rainfall < 50:
            risks.append('low_rainfall')
        if temp > 35:
            risks.append('heat_stress')
        return {'risks': risks, 'score': max(0, 100 - (len(risks) * 20))}

    def generate_farmer_friendly_insights(self, recs: Dict[str, Any], language: Optional[str] = None) -> str:
        summary = (
            f"Irrigation: {recs['irrigation']['schedule']}. "
            f"Fertilization: {recs['fertilization']['recommendations'][0]['advice']}. "
            f"Planting window: {recs['planting']['recommended_window']}. "
            f"Harvest in ~{recs['harvest']['remaining_days']} days. "
            f"Market trend: {recs['market_price']['trend']}. "
            f"Risks: {', '.join(recs['risk_assessment']['risks']) or 'none'}."
        )
        if language and self.translator:
            try:
                return self.translator.translate_content(summary, target_language=language, source_language='en')
            except Exception:
                return summary
        return summary

    def load_crop_specific_models(self):
        return {}


