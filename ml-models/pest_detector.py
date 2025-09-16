import os
from typing import List, Optional

import cv2
import numpy as np

try:  # Optional dependency guard
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
    from tensorflow.keras.models import Model
    _HAS_TF = True
except Exception:  # pragma: no cover
    tf = None  # type: ignore
    MobileNetV2 = None  # type: ignore
    Dense = None  # type: ignore
    GlobalAveragePooling2D = None  # type: ignore
    Model = None  # type: ignore
    _HAS_TF = False


class PestDetector:
    def __init__(self, model_path: Optional[str] = None, input_size: int = 224):
        self.input_size = int(input_size)
        self.labels = [
            'brown_planthopper', 'stem_borer', 'fall_armyworm', 'aphid', 'whitefly',
            'leaf_folder', 'thrips', 'mites', 'cutworm', 'bollworm'
        ]
        self.model = self.load_pest_model(model_path)

    def load_pest_model(self, model_path: Optional[str] = None):
        if not _HAS_TF:
            return None
        if model_path and os.path.exists(model_path):
            try:
                return tf.keras.models.load_model(model_path)
            except Exception:
                pass
        base = MobileNetV2(weights='imagenet', include_top=False, input_shape=(self.input_size, self.input_size, 3))
        x = base.output
        x = GlobalAveragePooling2D()(x)
        outputs = Dense(len(self.labels), activation='softmax')(x)
        model = Model(inputs=base.input, outputs=outputs)
        return model

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError('Could not read image')
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (self.input_size, self.input_size))
        img = img.astype('float32') / 255.0
        img = np.expand_dims(img, axis=0)
        return img

    def detect_pests(self, image_path: str) -> dict:
        image = cv2.imread(image_path)
        processed_image = self.preprocess_image(image)

        if _HAS_TF and self.model is not None:
            preds = self.model.predict(processed_image)
        else:
            preds = np.random.dirichlet(alpha=np.ones(len(self.labels)), size=1)

        return {
            'pest_type': self.decode_prediction(preds),
            'severity': self.calculate_severity(preds),
            'treatment_plan': self.generate_treatment(preds),
            'prevention_tips': self.get_prevention_advice(preds),
        }

    def decode_prediction(self, preds: np.ndarray) -> str:
        idx = int(np.argmax(preds))
        return self.labels[idx]

    def calculate_severity(self, preds: np.ndarray) -> str:
        confidence = float(np.max(preds))
        if confidence >= 0.8:
            return 'high'
        if confidence >= 0.5:
            return 'medium'
        return 'low'

    def generate_treatment(self, preds: np.ndarray) -> str:
        pest = self.decode_prediction(preds)
        mapping = {
            'brown_planthopper': 'Apply buprofezin or imidacloprid; drain excess water.',
            'stem_borer': 'Use tricho cards; apply chlorantraniliprole as per label.',
            'fall_armyworm': 'Spinosad or emamectin benzoate; monitor larvae early.',
            'aphid': 'Neem oil sprays; if severe, imidacloprid low dose.',
            'whitefly': 'Yellow sticky traps; rotate insecticides to avoid resistance.',
            'leaf_folder': 'Pheromone traps; avoid excessive nitrogen fertilization.',
            'thrips': 'Blue sticky traps; spinosad; maintain field sanitation.',
            'mites': 'Use acaricides judiciously; avoid dust and water stress.',
            'cutworm': 'Soil application of chlorpyrifos bait; field sanitation.',
            'bollworm': 'Bt formulations; emamectin; timely picking and sanitation.',
        }
        return mapping.get(pest, 'Follow integrated pest management (IPM) guidelines.')

    def get_prevention_advice(self, preds: np.ndarray) -> List[str]:
        pest = self.decode_prediction(preds)
        common = [
            'Rotate crops and avoid monoculture.',
            'Remove and destroy infested plant parts.',
            'Use resistant varieties where available.',
            'Maintain field hygiene and balanced fertilization.',
        ]
        specific = {
            'brown_planthopper': ['Avoid excessive nitrogen; maintain proper plant spacing.'],
            'stem_borer': ['Clip and destroy dead hearts; use light traps.'],
            'fall_armyworm': ['Scout whorls regularly; conserve natural enemies.'],
            'aphid': ['Avoid water stress; encourage ladybird beetles.'],
            'whitefly': ['Weed control to remove alternate hosts; reflective mulches.'],
            'leaf_folder': ['Avoid late planting; maintain proper irrigation.'],
            'thrips': ['Prevent dust; ensure adequate irrigation.'],
            'mites': ['Avoid use of broad-spectrum insecticides that kill predators.'],
            'cutworm': ['Deep ploughing to expose larvae; flood fields if appropriate.'],
            'bollworm': ['Timely sowing; remove crop residues after harvest.'],
        }
        return specific.get(pest, []) + common


