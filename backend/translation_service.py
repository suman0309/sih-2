import os
from typing import Any, Dict, List, Optional

import torch

try:  # Optional dependency
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    _HAS_TRANSFORMERS = True
except Exception:  # pragma: no cover
    AutoModelForSeq2SeqLM = None  # type: ignore
    AutoTokenizer = None  # type: ignore
    _HAS_TRANSFORMERS = False


class MultilingualService:
    def __init__(self, device: Optional[str] = None, max_batch_size: int = 8):
        # Support for 27 Indian languages including tribal languages
        self.supported_languages = {
            # Constitutional languages (22)
            'hindi': 'hi', 'bengali': 'bn', 'tamil': 'ta', 'telugu': 'te',
            'marathi': 'mr', 'gujarati': 'gu', 'kannada': 'kn', 'malayalam': 'ml',
            'punjabi': 'pa', 'odia': 'or', 'assamese': 'as', 'urdu': 'ur',
            'sanskrit': 'sa', 'sindhi': 'sd', 'nepali': 'ne', 'manipuri': 'mni',
            'konkani': 'gom', 'maithili': 'mai', 'dogri': 'doi', 'kashmiri': 'ks',
            'santali': 'sat', 'bodo': 'brx',

            # Additional tribal languages for Odisha
            'kui': 'kxv', 'santal': 'sat', 'ho': 'hoc', 'mundari': 'unr',
            'saura': 'srr'
        }

        # Models for Indic<->English directions. Pivot for Indic->Indic.
        self.model_indic_en = os.getenv('INDIC_EN_MODEL', 'ai4bharat/indictrans2-indic-en-1B')
        self.model_en_indic = os.getenv('EN_INDIC_MODEL', 'ai4bharat/indictrans2-en-indic-1B')

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_batch_size = int(max_batch_size)

        self.tokenizer_ie = None
        self.model_ie = None
        self.tokenizer_ei = None
        self.model_ei = None

        # Lazy-load on demand; environments without models should still import this module

    def translate_content(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        if not text:
            return ""

        src = self._normalize_lang(source_language) if source_language else None
        tgt = self._normalize_lang(target_language)
        if tgt is None:
            return text
        if src == tgt:
            return text
        if not _HAS_TRANSFORMERS:
            return text

        self._ensure_models_loaded()
        if self.model_ie is None or self.model_ei is None:
            return text

        # Heuristic source detection if not provided
        if src is None:
            ascii_ratio = sum(ch.isascii() for ch in text) / max(1, len(text))
            src = 'en' if ascii_ratio > 0.9 else 'hi'

        try:
            if src == 'en' and tgt != 'en':
                return self._translate_batch([text], self.tokenizer_ei, self.model_ei)[0]
            if tgt == 'en' and src != 'en':
                return self._translate_batch([text], self.tokenizer_ie, self.model_ie)[0]
            if src != 'en' and tgt != 'en':
                mid = self._translate_batch([text], self.tokenizer_ie, self.model_ie)[0]
                return self._translate_batch([mid], self.tokenizer_ei, self.model_ei)[0]
            # Default
            if src == 'en':
                return self._translate_batch([text], self.tokenizer_ei, self.model_ei)[0]
            return self._translate_batch([text], self.tokenizer_ie, self.model_ie)[0]
        except Exception:
            return text

    def voice_interface(self, audio_input: bytes, source_language: str):
        raise NotImplementedError("Voice interface is not implemented yet.")

    # ------------------------------ Helpers ------------------------------- #
    def _normalize_lang(self, lang: Optional[str]) -> Optional[str]:
        if not lang:
            return None
        key = str(lang).strip().lower()
        if key in self.supported_languages:
            return self.supported_languages[key]
        if key in self.supported_languages.values() or key == 'en':
            return key
        aliases = {'or': 'or', 'odiya': 'or', 'odia': 'or', 'hindi': 'hi'}
        return aliases.get(key)

    def _ensure_models_loaded(self) -> None:
        if not _HAS_TRANSFORMERS:
            return
        if self.model_ie is None:
            self.tokenizer_ie = AutoTokenizer.from_pretrained(self.model_indic_en)
            self.model_ie = AutoModelForSeq2SeqLM.from_pretrained(self.model_indic_en).to(self.device)
        if self.model_ei is None:
            self.tokenizer_ei = AutoTokenizer.from_pretrained(self.model_en_indic)
            self.model_ei = AutoModelForSeq2SeqLM.from_pretrained(self.model_en_indic).to(self.device)

    def _translate_batch(
        self,
        texts: List[str],
        tokenizer: Any,
        model: Any,
        max_new_tokens: int = 256,
    ) -> List[str]:
        outputs: List[str] = []
        if not texts:
            return outputs
        for start in range(0, len(texts), self.max_batch_size):
            batch = texts[start:start + self.max_batch_size]
            inputs = tokenizer(batch, return_tensors='pt', padding=True, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            gen = model.generate(**inputs, max_new_tokens=max_new_tokens)
            decoded = tokenizer.batch_decode(gen, skip_special_tokens=True)
            outputs.extend(decoded)
        return outputs


