"""
Sentiment Analyzer Module
Analyzes market sentiment from various sources
Uses NLTK and TextBlob for NLP-based sentiment analysis
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try to import NLP libraries
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("WARNING: TextBlob not installed. Sentiment analysis will be limited.")

try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    # Download required data (silently)
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        try:
            nltk.download('vader_lexicon', quiet=True)
        except:
            pass
    NLTK_AVAILABLE = True
    vader = SentimentIntensityAnalyzer()
except:
    NLTK_AVAILABLE = False
    vader = None
    print("WARNING: NLTK VADER not available. Using TextBlob only.")


class SentimentAnalyzer:
    """
    Multi-source sentiment analyzer for Indian market
    Analyzes: News headlines, Option chain sentiment, Technical sentiment
    """
    
    def __init__(self):
        self.sentiment_history = []
        self.last_sentiment = None
        self.news_cache = []
        self.cache_timestamp = None
        
        # Financial keyword weights (Indian market specific)
        self.bullish_keywords = [
            'rally', 'surge', 'gain', 'rise', 'bullish', 'up', 'high', 'record',
            'buy', 'long', 'breakout', 'support', 'fii buying', 'dii buying',
            'nifty up', 'banknifty up', 'green', 'positive', 'growth', 'profit',
            'beat estimate', 'upgrade', 'outperform', 'strong', 'recover'
        ]
        
        self.bearish_keywords = [
            'crash', 'fall', 'drop', 'decline', 'bearish', 'down', 'low', 'sell',
            'short', 'breakdown', 'resistance', 'fii selling', 'dii selling',
            'nifty down', 'banknifty down', 'red', 'negative', 'loss', 'miss',
            'downgrade', 'underperform', 'weak', 'fear', 'panic', 'correction'
        ]
        
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        
        Returns:
            Dict with polarity score (-1 to 1) and classification
        """
        if not text:
            return {'polarity': 0, 'classification': 'NEUTRAL', 'confidence': 0}
            
        text_lower = text.lower()
        
        # Method 1: Keyword-based scoring
        keyword_score = self._keyword_score(text_lower)
        
        # Method 2: VADER (if available)
        vader_score = 0
        if NLTK_AVAILABLE and vader:
            try:
                scores = vader.polarity_scores(text)
                vader_score = scores['compound']
            except:
                pass
                
        # Method 3: TextBlob (if available)
        textblob_score = 0
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                textblob_score = blob.sentiment.polarity
            except:
                pass
                
        # Combine scores with weights
        if NLTK_AVAILABLE and TEXTBLOB_AVAILABLE:
            # All methods available
            final_score = (keyword_score * 0.4 + vader_score * 0.35 + textblob_score * 0.25)
        elif NLTK_AVAILABLE:
            final_score = (keyword_score * 0.5 + vader_score * 0.5)
        elif TEXTBLOB_AVAILABLE:
            final_score = (keyword_score * 0.5 + textblob_score * 0.5)
        else:
            final_score = keyword_score
            
        # Classification
        if final_score > 0.1:
            classification = 'BULLISH'
        elif final_score < -0.1:
            classification = 'BEARISH'
        else:
            classification = 'NEUTRAL'
            
        confidence = min(abs(final_score), 1.0)
        
        return {
            'polarity': round(final_score, 3),
            'classification': classification,
            'confidence': round(confidence, 2),
            'keyword_score': round(keyword_score, 3),
            'vader_score': round(vader_score, 3) if NLTK_AVAILABLE else None,
            'textblob_score': round(textblob_score, 3) if TEXTBLOB_AVAILABLE else None
        }
        
    def _keyword_score(self, text: str) -> float:
        """Calculate sentiment score based on financial keywords"""
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in text)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in text)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0
            
        score = (bullish_count - bearish_count) / total
        return score
        
    def analyze_headlines(self, headlines: List[str]) -> Dict:
        """
        Analyze multiple news headlines
        
        Returns:
            Aggregated sentiment with individual scores
        """
        if not headlines:
            return self._default_sentiment()
            
        scores = []
        individual_results = []
        
        for headline in headlines:
            result = self.analyze_text(headline)
            scores.append(result['polarity'])
            individual_results.append({
                'text': headline[:100],  # Truncate
                'sentiment': result
            })
            
        avg_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Classification based on average
        if avg_score > 0.1:
            classification = 'BULLISH'
        elif avg_score < -0.1:
            classification = 'BEARISH'
        else:
            classification = 'NEUTRAL'
            
        # Confidence based on consistency
        confidence = max(0.3, 1 - std_score)
        
        return {
            'average_polarity': round(avg_score, 3),
            'classification': classification,
            'confidence': round(confidence, 2),
            'std_deviation': round(std_score, 3),
            'bullish_count': sum(1 for s in scores if s > 0.1),
            'bearish_count': sum(1 for s in scores if s < -0.1),
            'neutral_count': sum(1 for s in scores if -0.1 <= s <= 0.1),
            'total_analyzed': len(headlines),
            'individual_results': individual_results[:5]  # First 5 only
        }
        
    def analyze_option_chain_sentiment(self, 
                                        pcr: float,
                                        ce_oi_change: int,
                                        pe_oi_change: int,
                                        max_pain: float,
                                        current_price: float) -> Dict:
        """
        Analyze sentiment from option chain data
        """
        sentiment_score = 0
        signals = []
        
        # PCR Analysis
        if pcr > 1.3:
            sentiment_score += 0.3
            signals.append(f'High PCR ({pcr:.2f}) - Bullish')
        elif pcr < 0.7:
            sentiment_score -= 0.3
            signals.append(f'Low PCR ({pcr:.2f}) - Bearish')
        else:
            signals.append(f'Neutral PCR ({pcr:.2f})')
            
        # OI Change Analysis
        if pe_oi_change > ce_oi_change * 1.5:
            sentiment_score += 0.2
            signals.append('PE OI building - Bullish')
        elif ce_oi_change > pe_oi_change * 1.5:
            sentiment_score -= 0.2
            signals.append('CE OI building - Bearish')
            
        # Max Pain Analysis
        price_from_mp = (current_price - max_pain) / max_pain * 100
        if price_from_mp > 1:
            sentiment_score -= 0.1
            signals.append(f'Above max pain by {price_from_mp:.1f}% - May pullback')
        elif price_from_mp < -1:
            sentiment_score += 0.1
            signals.append(f'Below max pain by {abs(price_from_mp):.1f}% - May rise')
            
        # Classification
        if sentiment_score > 0.2:
            classification = 'BULLISH'
        elif sentiment_score < -0.2:
            classification = 'BEARISH'
        else:
            classification = 'NEUTRAL'
            
        return {
            'score': round(sentiment_score, 2),
            'classification': classification,
            'confidence': round(abs(sentiment_score), 2),
            'signals': signals,
            'pcr': pcr,
            'oi_bias': 'PUTS' if pe_oi_change > ce_oi_change else 'CALLS'
        }
        
    def analyze_technical_sentiment(self, indicators: Dict) -> Dict:
        """
        Derive sentiment from technical indicators
        """
        sentiment_score = 0
        signals = []
        
        # RSI
        rsi = indicators.get('rsi', 50)
        if rsi:
            if rsi > 70:
                sentiment_score -= 0.2
                signals.append(f'RSI overbought ({rsi:.1f})')
            elif rsi < 30:
                sentiment_score += 0.2
                signals.append(f'RSI oversold ({rsi:.1f})')
            elif rsi > 50:
                sentiment_score += 0.1
                signals.append('RSI bullish bias')
            else:
                sentiment_score -= 0.1
                signals.append('RSI bearish bias')
                
        # MACD
        macd = indicators.get('macd', {})
        if isinstance(macd, dict):
            histogram = macd.get('histogram', 0)
            if histogram:
                if histogram > 0:
                    sentiment_score += 0.15
                    signals.append('MACD positive')
                else:
                    sentiment_score -= 0.15
                    signals.append('MACD negative')
                    
        # Supertrend
        supertrend = indicators.get('supertrend', {})
        if isinstance(supertrend, dict):
            trend = supertrend.get('trend', '')
            if trend == 'UP':
                sentiment_score += 0.2
                signals.append('Supertrend bullish')
            elif trend == 'DOWN':
                sentiment_score -= 0.2
                signals.append('Supertrend bearish')
                
        # ADX (trend strength)
        adx = indicators.get('adx', {})
        if isinstance(adx, dict):
            adx_val = adx.get('adx', 25)
            plus_di = adx.get('plus_di', 25)
            minus_di = adx.get('minus_di', 25)
            
            if adx_val > 25:
                if plus_di > minus_di:
                    sentiment_score += 0.1
                    signals.append('Strong bullish trend')
                else:
                    sentiment_score -= 0.1
                    signals.append('Strong bearish trend')
                    
        # Classification
        if sentiment_score > 0.2:
            classification = 'BULLISH'
        elif sentiment_score < -0.2:
            classification = 'BEARISH'
        else:
            classification = 'NEUTRAL'
            
        return {
            'score': round(sentiment_score, 2),
            'classification': classification,
            'confidence': round(min(abs(sentiment_score) * 2, 1), 2),
            'signals': signals
        }
        
    def get_combined_sentiment(self,
                                news_headlines: List[str] = None,
                                option_data: Dict = None,
                                indicators: Dict = None) -> Dict:
        """
        Combine all sentiment sources into a single score
        """
        scores = []
        weights = []
        details = {}
        
        # News sentiment
        if news_headlines:
            news_sent = self.analyze_headlines(news_headlines)
            scores.append(news_sent['average_polarity'])
            weights.append(0.3)
            details['news'] = news_sent
            
        # Option chain sentiment
        if option_data:
            opt_sent = self.analyze_option_chain_sentiment(
                pcr=option_data.get('pcr', 1.0),
                ce_oi_change=option_data.get('ce_oi_change', 0),
                pe_oi_change=option_data.get('pe_oi_change', 0),
                max_pain=option_data.get('max_pain', 0),
                current_price=option_data.get('current_price', 0)
            )
            scores.append(opt_sent['score'])
            weights.append(0.4)
            details['options'] = opt_sent
            
        # Technical sentiment
        if indicators:
            tech_sent = self.analyze_technical_sentiment(indicators)
            scores.append(tech_sent['score'])
            weights.append(0.3)
            details['technical'] = tech_sent
            
        # Weighted average
        if scores:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            weighted_score = 0
            
        # Classification
        if weighted_score > 0.15:
            classification = 'BULLISH'
        elif weighted_score < -0.15:
            classification = 'BEARISH'
        else:
            classification = 'NEUTRAL'
            
        result = {
            'combined_score': round(weighted_score, 3),
            'classification': classification,
            'confidence': round(min(abs(weighted_score) * 2.5, 1), 2),
            'sources_used': len(scores),
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store in history
        self.sentiment_history.append(result)
        self.last_sentiment = result
        
        # Keep only last 50
        if len(self.sentiment_history) > 50:
            self.sentiment_history = self.sentiment_history[-50:]
            
        return result
        
    def _default_sentiment(self) -> Dict:
        """Return default neutral sentiment"""
        return {
            'average_polarity': 0,
            'classification': 'NEUTRAL',
            'confidence': 0.3,
            'std_deviation': 0,
            'bullish_count': 0,
            'bearish_count': 0,
            'neutral_count': 0,
            'total_analyzed': 0
        }
        
    def get_sentiment_summary(self) -> Dict:
        """Get summary of recent sentiment history"""
        if not self.sentiment_history:
            return {'current': None, 'trend': 'NEUTRAL'}
            
        recent = self.sentiment_history[-10:]
        scores = [s['combined_score'] for s in recent]
        
        avg = np.mean(scores)
        trend = 'NEUTRAL'
        if len(scores) >= 3:
            if scores[-1] > scores[0]:
                trend = 'IMPROVING'
            elif scores[-1] < scores[0]:
                trend = 'DETERIORATING'
                
        return {
            'current': self.last_sentiment,
            'average_score': round(avg, 3),
            'trend': trend,
            'history_length': len(self.sentiment_history)
        }


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of a single text"""
    return sentiment_analyzer.analyze_text(text)


def analyze_news_sentiment(headlines: List[str]) -> Dict:
    """Analyze sentiment of news headlines"""
    return sentiment_analyzer.analyze_headlines(headlines)


def get_combined_sentiment(news: List[str] = None, 
                           options: Dict = None, 
                           indicators: Dict = None) -> Dict:
    """Get combined sentiment from all sources"""
    return sentiment_analyzer.get_combined_sentiment(news, options, indicators)


def get_sentiment_summary() -> Dict:
    """Get sentiment summary"""
    return sentiment_analyzer.get_sentiment_summary()
