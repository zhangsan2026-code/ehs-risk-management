import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class StockMonitor:
    def __init__(self, api_key=None):
        self.api_key = api_key or "demo"
        self.monitored_stocks = {}
        self.price_history = defaultdict(list)
        self.alerts = []
        self.last_update = {}
        self.portfolio = {}
    
    def get_stock_data(self, symbol):
        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={self.api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    result = data['results'][0]
                    return {
                        'symbol': symbol,
                        'price': result['c'],
                        'open': result['o'],
                        'high': result['h'],
                        'low': result['l'],
                        'volume': result['v'],
                        'change': result['c'] - result['o'],
                        'change_pct': ((result['c'] - result['o']) / result['o']) * 100,
                        'timestamp': datetime.fromtimestamp(result['t'] / 1000)
                    }
            return self.get_demo_data(symbol)
        except Exception as e:
            return self.get_demo_data(symbol)
    
    def get_demo_data(self, symbol):
        base_prices = {
            'AAPL': 178.50, 'GOOGL': 141.80, 'MSFT': 378.90, 'TSLA': 248.30, 'NVDA': 875.20,
            'AMZN': 178.25, 'META': 505.75, 'AMD': 178.90, 'JPM': 215.50, 'V': 286.30,
            'JNJ': 151.80, 'WMT': 156.40, 'PG': 168.20, 'MA': 388.60, 'NFLX': 615.80
        }
        base_price = base_prices.get(symbol, 100.0)
        change = np.random.uniform(-2, 2)
        price = base_price * (1 + change / 100)
        return {
            'symbol': symbol,
            'price': round(price, 2),
            'open': round(base_price, 2),
            'high': round(price * 1.01, 2),
            'low': round(price * 0.99, 2),
            'volume': int(np.random.uniform(1000000, 10000000)),
            'change': round(price - base_price, 2),
            'change_pct': round(change, 2),
            'timestamp': datetime.now()
        }
    
    def add_stock(self, symbol, alert_high=None, alert_low=None, shares=0, avg_cost=0):
        self.monitored_stocks[symbol] = {
            'alert_high': alert_high,
            'alert_low': alert_low,
            'status': 'monitoring',
            'shares': shares,
            'avg_cost': avg_cost
        }
    
    def remove_stock(self, symbol):
        if symbol in self.monitored_stocks:
            del self.monitored_stocks[symbol]
            if symbol in self.price_history:
                del self.price_history[symbol]
    
    def update_all_stocks(self):
        for symbol in self.monitored_stocks.keys():
            data = self.get_stock_data(symbol)
            self.price_history[symbol].append(data)
            if len(self.price_history[symbol]) > 500:
                self.price_history[symbol].pop(0)
            self.last_update[symbol] = datetime.now()
            self.check_alerts(symbol, data)
    
    def check_alerts(self, symbol, data):
        config = self.monitored_stocks[symbol]
        price = data['price']
        timestamp = data['timestamp']
        
        if config['alert_high'] and price >= config['alert_high']:
            alert = {
                'symbol': symbol,
                'type': 'high',
                'price': price,
                'threshold': config['alert_high'],
                'timestamp': timestamp,
                'message': f"⚠️ {symbol} 触及高位预警: ${price:.2f} (阈值: ${config['alert_high']})"
            }
            self.alerts.append(alert)
        
        if config['alert_low'] and price <= config['alert_low']:
            alert = {
                'symbol': symbol,
                'type': 'low',
                'price': price,
                'threshold': config['alert_low'],
                'timestamp': timestamp,
                'message': f"⚠️ {symbol} 触及低位预警: ${price:.2f} (阈值: ${config['alert_low']})"
            }
            self.alerts.append(alert)
        
        indicators = self.calculate_indicators(symbol)
        if indicators and indicators['rsi']:
            if indicators['rsi'] >= 70:
                alert = {
                    'symbol': symbol,
                    'type': 'overbought',
                    'price': price,
                    'threshold': 70,
                    'timestamp': timestamp,
                    'message': f"📈 {symbol} RSI超买: {indicators['rsi']:.2f}"
                }
                self.alerts.append(alert)
            elif indicators['rsi'] <= 30:
                alert = {
                    'symbol': symbol,
                    'type': 'oversold',
                    'price': price,
                    'threshold': 30,
                    'timestamp': timestamp,
                    'message': f"📉 {symbol} RSI超卖: {indicators['rsi']:.2f}"
                }
                self.alerts.append(alert)
    
    def calculate_indicators(self, symbol):
        history = self.price_history[symbol]
        if len(history) < 20:
            return None
        
        prices = np.array([h['price'] for h in history])
        volumes = np.array([h['volume'] for h in history])
        times = [h['timestamp'] for h in history]
        
        sma_5 = np.mean(prices[-5:])
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else None
        sma_100 = np.mean(prices[-100:]) if len(prices) >= 100 else None
        
        std_dev = np.std(prices[-20:])
        upper_bb = sma_20 + 2 * std_dev
        lower_bb = sma_20 - 2 * std_dev
        
        if len(prices) >= 14:
            deltas = np.diff(prices)
            gains = deltas[deltas > 0].sum() / len(deltas)
            losses = -deltas[deltas < 0].sum() / len(deltas)
            rs = gains / losses if losses != 0 else 1
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = None
        
        if len(prices) >= 12:
            ema_12 = np.mean(prices[-12:])
            ema_26 = np.mean(prices[-26:]) if len(prices) >= 26 else None
            macd = ema_12 - ema_26 if ema_26 else None
        else:
            macd = None
        
        volatility = np.std(prices[-20:]) / np.mean(prices[-20:]) * 100
        
        if len(prices) >= 2:
            momentum = prices[-1] - prices[-10] if len(prices) >= 10 else prices[-1] - prices[-2]
        else:
            momentum = 0
        
        current_price = prices[-1]
        price_range = prices.max() - prices.min()
        price_percentile = (current_price - prices.min()) / price_range * 100 if price_range > 0 else 50
        
        trend_score = 0
        if sma_5 > sma_20:
            trend_score += 1
        if sma_20 > sma_50:
            trend_score += 1
        if current_price > sma_20:
            trend_score += 1
        
        trend = 'bullish' if sma_5 > sma_20 else 'bearish' if sma_5 < sma_20 else 'neutral'
        
        volume_avg = np.mean(volumes[-20:])
        volume_ratio = volumes[-1] / volume_avg if volume_avg > 0 else 1
        
        return {
            'sma_5': round(sma_5, 2),
            'sma_20': round(sma_20, 2),
            'sma_50': round(sma_50, 2) if sma_50 else None,
            'sma_100': round(sma_100, 2) if sma_100 else None,
            'upper_bb': round(upper_bb, 2),
            'lower_bb': round(lower_bb, 2),
            'rsi': round(rsi, 2) if rsi else None,
            'macd': round(macd, 2) if macd else None,
            'volatility': round(volatility, 2),
            'momentum': round(momentum, 2),
            'price_percentile': round(price_percentile, 2),
            'trend_score': trend_score,
            'trend': trend,
            'current_price': round(current_price, 2),
            'volume': int(volumes[-1]),
            'volume_ratio': round(volume_ratio, 2),
            'avg_volume': int(volume_avg),
            'high_20d': round(prices[-20:].max(), 2),
            'low_20d': round(prices[-20:].min(), 2),
            'price_range': round(price_range, 2)
        }
    
    def get_portfolio_summary(self):
        summary = []
        for symbol in self.monitored_stocks.keys():
            history = self.price_history.get(symbol)
            if history:
                latest = history[-1]
                indicators = self.calculate_indicators(symbol)
                config = self.monitored_stocks[symbol]
                position_value = latest['price'] * config['shares']
                unrealized_pnl = (latest['price'] - config['avg_cost']) * config['shares'] if config['avg_cost'] > 0 else 0
                unrealized_pnl_pct = ((latest['price'] - config['avg_cost']) / config['avg_cost']) * 100 if config['avg_cost'] > 0 else 0
                
                summary.append({
                    'symbol': symbol,
                    'price': latest['price'],
                    'open': latest['open'],
                    'high': latest['high'],
                    'low': latest['low'],
                    'change': latest['change'],
                    'change_pct': latest['change_pct'],
                    'volume': latest['volume'],
                    'trend': indicators['trend'] if indicators else 'unknown',
                    'rsi': indicators['rsi'] if indicators else None,
                    'shares': config['shares'],
                    'avg_cost': config['avg_cost'],
                    'position_value': round(position_value, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'unrealized_pnl_pct': round(unrealized_pnl_pct, 2)
                })
        return pd.DataFrame(summary)
    
    def get_market_overview(self):
        summary = self.get_portfolio_summary()
        if summary.empty:
            return None
        
        total_value = summary['position_value'].sum()
        total_pnl = summary['unrealized_pnl'].sum()
        total_pnl_pct = (total_pnl / (total_value - total_pnl)) * 100 if (total_value - total_pnl) > 0 else 0
        
        bullish_count = len(summary[summary['trend'] == 'bullish'])
        bearish_count = len(summary[summary['trend'] == 'bearish'])
        neutral_count = len(summary[summary['trend'] == 'neutral'])
        
        avg_rsi = summary['rsi'].mean()
        avg_volume = summary['volume'].mean()
        
        return {
            'total_stocks': len(summary),
            'total_value': round(total_value, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'avg_rsi': round(avg_rsi, 2),
            'avg_volume': int(avg_volume),
            'market_mood': 'bullish' if bullish_count > bearish_count else 'bearish' if bearish_count > bullish_count else 'neutral'
        }
    
    def get_price_chart_data(self, symbol, period='1d'):
        history = self.price_history.get(symbol, [])
        if not history:
            return {'timestamps': [], 'prices': [], 'volumes': []}
        
        timestamps = [h['timestamp'].strftime('%H:%M:%S') for h in history]
        prices = [h['price'] for h in history]
        volumes = [h['volume'] for h in history]
        
        return {
            'timestamps': timestamps,
            'prices': prices,
            'volumes': volumes
        }
    
    def get_recent_alerts(self, limit=20):
        recent_alerts = self.alerts[-limit:] if len(self.alerts) > limit else self.alerts
        return [{
            'symbol': alert['symbol'],
            'type': alert['type'],
            'price': alert['price'],
            'threshold': alert['threshold'],
            'timestamp': alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'message': alert['message']
        } for alert in recent_alerts]

def main():
    monitor = StockMonitor()
    monitor.add_stock('AAPL', alert_high=185, alert_low=170, shares=100, avg_cost=175.00)
    monitor.add_stock('GOOGL', alert_high=145, alert_low=135, shares=50, avg_cost=140.00)
    monitor.add_stock('MSFT', alert_high=390, alert_low=360, shares=80, avg_cost=370.00)
    monitor.add_stock('TSLA', alert_high=260, alert_low=230, shares=120, avg_cost=240.00)
    monitor.add_stock('NVDA', alert_high=900, alert_low=800, shares=30, avg_cost=850.00)
    
    for _ in range(10):
        monitor.update_all_stocks()
        time.sleep(0.5)
    
    print("投资组合概览")
    summary = monitor.get_portfolio_summary()
    print(summary)
    
    print("\n市场概况")
    overview = monitor.get_market_overview()
    print(overview)
    
    print("\n技术指标分析")
    for symbol in monitor.monitored_stocks.keys():
        indicators = monitor.calculate_indicators(symbol)
        if indicators:
            print(f"\n{symbol}:")
            print(f"  当前价格: ${indicators['current_price']:.2f}")
            print(f"  RSI: {indicators['rsi']}")
            print(f"  趋势: {indicators['trend']}")

if __name__ == "__main__":
    main()