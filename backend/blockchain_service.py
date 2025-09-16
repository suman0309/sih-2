import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class AgriBlockchain:
    def __init__(self, difficulty: int = 0):
        self.chain: List[Dict[str, Any]] = []
        self.difficulty = int(difficulty)
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        if self.chain:
            return
        genesis = {
            'index': 1,
            'timestamp': datetime.utcnow().isoformat(),
            'farmer_id': 'genesis',
            'crop_data': {},
            'prediction': {},
            'actual': None,
            'error_abs': None,
            'prev_hash': '0' * 64,
            'nonce': 0,
        }
        genesis['hash'] = self._compute_block_hash(genesis)
        self.chain.append(genesis)

    def add_prediction_record(self, farmer_id: str, crop_data: Dict[str, Any], prediction_result: Dict[str, Any]) -> str:
        prev_block = self.chain[-1]
        block = {
            'index': prev_block['index'] + 1,
            'timestamp': datetime.utcnow().isoformat(),
            'farmer_id': farmer_id,
            'crop_data': crop_data,
            'prediction': prediction_result,
            'actual': None,
            'error_abs': None,
            'prev_hash': prev_block['hash'],
            'nonce': 0,
        }
        if self.difficulty > 0:
            self._mine(block)
        else:
            block['hash'] = self._compute_block_hash(block)
        self.chain.append(block)
        return block['hash']

    def verify_prediction_accuracy(self, prediction_hash: str, actual_yield: float) -> Dict[str, Any]:
        block = self._find_block_by_hash(prediction_hash)
        if block is None:
            return {"error": "hash_not_found"}
        try:
            predicted = float(block['prediction'].get('yield'))
        except Exception:
            return {"error": "prediction_missing"}

        error_abs = abs(float(actual_yield) - predicted)
        block['actual'] = float(actual_yield)
        block['error_abs'] = float(error_abs)
        block['verification_hash'] = self._compute_block_hash(block)

        errors: List[float] = []
        for b in self.chain[1:]:
            if b.get('actual') is not None:
                pred = b['prediction'].get('yield')
                try:
                    pred = float(pred)
                    act = float(b['actual'])
                    if act != 0:
                        errors.append(abs((act - pred) / act))
                except Exception:
                    continue
        mape = (sum(errors) / len(errors) * 100.0) if errors else None

        return {
            'block_index': block['index'],
            'error_abs': error_abs,
            'mape_percent': mape,
            'chain_valid': self.is_chain_valid(),
        }

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr['prev_hash'] != prev['hash']:
                return False
            if self.difficulty > 0 and not str(curr['hash']).startswith('0' * self.difficulty):
                return False
            if curr['hash'] != self._compute_block_hash({k: v for k, v in curr.items() if k != 'hash'}):
                return False
        return True

    def _find_block_by_hash(self, h: str) -> Optional[Dict[str, Any]]:
        for b in self.chain:
            if b.get('hash') == h:
                return b
        return None

    def _compute_block_hash(self, block_without_hash: Dict[str, Any]) -> str:
        data = {k: block_without_hash[k] for k in sorted(block_without_hash.keys()) if k != 'hash'}
        payload = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _mine(self, block: Dict[str, Any]) -> None:
        nonce = 0
        while True:
            block['nonce'] = nonce
            candidate_hash = self._compute_block_hash(block)
            if candidate_hash.startswith('0' * self.difficulty):
                block['hash'] = candidate_hash
                return
            nonce += 1


