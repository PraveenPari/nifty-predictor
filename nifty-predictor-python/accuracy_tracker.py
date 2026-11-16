"""
Persistent Accuracy Tracker
Logs predictions and outcomes to JSON file for long-term accuracy tracking
Survives app restarts
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class AccuracyTracker:
    """
    Persistent accuracy tracker that saves prediction history to disk.
    Enables long-term accuracy analysis across app restarts.
    """
    
    def __init__(self, log_file: str = "accuracy_log.json"):
        self.log_file = Path(__file__).parent / log_file
        self.predictions = []
        self.stats = {
            'total_predictions': 0,
            'validated_predictions': 0,
            'wins': 0,
            'losses': 0,
            'flats': 0,
            'daily_stats': {}
        }
        self._load_from_disk()
        
    def _load_from_disk(self):
        """Load existing predictions from disk"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.predictions = data.get('predictions', [])
                    self.stats = data.get('stats', self.stats)
                    print(f"[ACCURACY] Loaded {len(self.predictions)} predictions from disk")
        except Exception as e:
            print(f"[ACCURACY] Could not load history: {e}")
            
    def _save_to_disk(self):
        """Save predictions to disk"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump({
                    'predictions': self.predictions[-500:],  # Keep last 500
                    'stats': self.stats,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[ACCURACY] Could not save: {e}")
            
    def log_prediction(self, prediction: Dict, entry_price: float) -> str:
        """
        Log a new prediction
        Returns: prediction ID for later validation
        """
        pred_id = f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.predictions)}"
        
        entry = {
            'id': pred_id,
            'timestamp': datetime.now().isoformat(),
            'direction': prediction.get('direction', 'NEUTRAL'),
            'signal': prediction.get('signal', 'WAIT'),
            'confidence': prediction.get('confidence', 0),
            'entry_price': entry_price,
            'validated': False,
            'result': None,
            'validation_time': None,
            'exit_price': None,
            'percent_change': None
        }
        
        self.predictions.append(entry)
        self.stats['total_predictions'] += 1
        
        # Auto-save every 10 predictions
        if len(self.predictions) % 10 == 0:
            self._save_to_disk()
            
        return pred_id
        
    def validate_predictions(self, current_price: float, 
                            validation_window_minutes: int = 15,
                            win_threshold_percent: float = 0.05) -> Dict:
        """
        Validate pending predictions against current price
        Uses 0.05% threshold for meaningful 15m intraday wins/losses
        """
        now = datetime.now()
        newly_validated = 0
        
        for pred in self.predictions:
            if pred.get('validated', False):
                continue
                
            # Check if validation window has passed
            pred_time = datetime.fromisoformat(pred['timestamp'])
            validation_time = pred_time + timedelta(minutes=validation_window_minutes)
            
            if now < validation_time:
                continue
                
            # Validate this prediction
            entry_price = pred.get('entry_price', current_price)
            percent_change = ((current_price - entry_price) / entry_price) * 100
            
            direction = pred.get('direction', 'NEUTRAL')
            
            # Determine result with improved threshold (0.2% instead of 0.05%)
            if direction == 'BULLISH':
                if percent_change >= win_threshold_percent:
                    result = 'WIN'
                    self.stats['wins'] += 1
                elif percent_change <= -win_threshold_percent:
                    result = 'LOSS'
                    self.stats['losses'] += 1
                else:
                    result = 'FLAT'
                    self.stats['flats'] += 1
            elif direction == 'BEARISH':
                if percent_change <= -win_threshold_percent:
                    result = 'WIN'
                    self.stats['wins'] += 1
                elif percent_change >= win_threshold_percent:
                    result = 'LOSS'
                    self.stats['losses'] += 1
                else:
                    result = 'FLAT'
                    self.stats['flats'] += 1
            else:
                result = 'FLAT'
                self.stats['flats'] += 1
                
            # Update prediction record
            pred['validated'] = True
            pred['result'] = result
            pred['validation_time'] = now.isoformat()
            pred['exit_price'] = current_price
            pred['percent_change'] = round(percent_change, 3)
            
            self.stats['validated_predictions'] += 1
            newly_validated += 1
            
            # Update daily stats
            date_key = pred_time.strftime('%Y-%m-%d')
            if date_key not in self.stats['daily_stats']:
                self.stats['daily_stats'][date_key] = {'wins': 0, 'losses': 0, 'flats': 0}
            self.stats['daily_stats'][date_key][result.lower() + 's'] = \
                self.stats['daily_stats'][date_key].get(result.lower() + 's', 0) + 1
                
        if newly_validated > 0:
            self._save_to_disk()
            
        return {
            'newly_validated': newly_validated,
            'pending': sum(1 for p in self.predictions if not p.get('validated', False))
        }
        
    def get_accuracy_stats(self) -> Dict:
        """Get comprehensive accuracy statistics"""
        total_decided = self.stats['wins'] + self.stats['losses']
        
        return {
            'total_predictions': self.stats['total_predictions'],
            'validated': self.stats['validated_predictions'],
            'pending': self.stats['total_predictions'] - self.stats['validated_predictions'],
            'wins': self.stats['wins'],
            'losses': self.stats['losses'],
            'flats': self.stats['flats'],
            'win_rate': round((self.stats['wins'] / total_decided * 100), 1) if total_decided > 0 else 0,
            'accuracy': round((self.stats['wins'] / self.stats['validated_predictions'] * 100), 1) 
                       if self.stats['validated_predictions'] > 0 else 0,
            'daily_stats': dict(list(self.stats['daily_stats'].items())[-7:])  # Last 7 days
        }
        
    def get_recent_results(self, n: int = 10) -> List[Dict]:
        """Get last N validated predictions"""
        validated = [p for p in self.predictions if p.get('validated', False)]
        return validated[-n:]
        
    def get_streak(self) -> Dict:
        """Get current win/loss streak"""
        validated = [p for p in self.predictions if p.get('validated', False) and p.get('result') in ['WIN', 'LOSS']]
        
        if not validated:
            return {'type': 'NONE', 'count': 0}
            
        current_result = validated[-1]['result']
        streak = 0
        
        for pred in reversed(validated):
            if pred['result'] == current_result:
                streak += 1
            else:
                break
                
        return {
            'type': 'WINNING' if current_result == 'WIN' else 'LOSING',
            'count': streak
        }


# Singleton instance
accuracy_tracker = AccuracyTracker()


def log_prediction(prediction: Dict, entry_price: float) -> str:
    """Log a new prediction"""
    return accuracy_tracker.log_prediction(prediction, entry_price)


def validate_predictions(current_price: float) -> Dict:
    """Validate pending predictions"""
    return accuracy_tracker.validate_predictions(current_price)


def get_accuracy_stats() -> Dict:
    """Get accuracy statistics"""
    return accuracy_tracker.get_accuracy_stats()


def get_recent_results(n: int = 10) -> List[Dict]:
    """Get recent validated predictions"""
    return accuracy_tracker.get_recent_results(n)
