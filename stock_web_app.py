from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import json
from stock_monitor import StockMonitor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stock_monitor_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=1000, ping_timeout=5000)

monitor = StockMonitor()
monitor.add_stock('AAPL', alert_high=185, alert_low=170, shares=100, avg_cost=175.00)
monitor.add_stock('GOOGL', alert_high=145, alert_low=135, shares=50, avg_cost=140.00)
monitor.add_stock('MSFT', alert_high=390, alert_low=360, shares=80, avg_cost=370.00)
monitor.add_stock('TSLA', alert_high=260, alert_low=230, shares=120, avg_cost=240.00)
monitor.add_stock('NVDA', alert_high=900, alert_low=800, shares=30, avg_cost=850.00)
monitor.add_stock('AMZN', alert_high=185, alert_low=165, shares=60, avg_cost=175.00)
monitor.add_stock('META', alert_high=520, alert_low=480, shares=40, avg_cost=500.00)
monitor.add_stock('AMD', alert_high=185, alert_low=165, shares=70, avg_cost=175.00)

update_interval = 1.0

def get_stock_data():
    monitor.update_all_stocks()
    summary = monitor.get_portfolio_summary()
    summary_dict = summary.to_dict('records')
    
    indicators_data = {}
    for symbol in monitor.monitored_stocks.keys():
        indicators = monitor.calculate_indicators(symbol)
        if indicators:
            indicators_data[symbol] = indicators
    
    overview = monitor.get_market_overview()
    
    chart_data = {}
    for symbol in monitor.monitored_stocks.keys():
        chart_data[symbol] = monitor.get_price_chart_data(symbol)
    
    alerts_data = monitor.get_recent_alerts(20)
    
    return {
        'summary': summary_dict,
        'indicators': indicators_data,
        'overview': overview,
        'chart_data': chart_data,
        'alerts': alerts_data,
        'update_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'update_time_ms': int(time.time() * 1000)
    }

def background_monitor():
    last_update = time.time()
    while True:
        current_time = time.time()
        elapsed = current_time - last_update
        
        if elapsed >= update_interval:
            try:
                data = get_stock_data()
                socketio.emit('update', data)
                last_update = current_time
            except Exception as e:
                print(f"Error sending update: {e}")
        
        time.sleep(0.1)

@app.route('/')
def index():
    initial_data = get_stock_data()
    return render_template('stock_dashboard.html', initial_data=initial_data)

@app.route('/api/stocks')
def api_stocks():
    return jsonify(get_stock_data())

@app.route('/api/indicators/<symbol>')
def api_indicators(symbol):
    indicators = monitor.calculate_indicators(symbol)
    return jsonify(indicators if indicators else {})

@app.route('/api/alerts')
def api_alerts():
    alerts = monitor.get_recent_alerts(20)
    return jsonify(alerts)

@app.route('/api/add_stock', methods=['POST'])
def api_add_stock():
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        alert_high = data.get('alert_high')
        alert_low = data.get('alert_low')
        shares = data.get('shares', 0)
        avg_cost = data.get('avg_cost', 0)
        
        if symbol:
            monitor.add_stock(symbol, alert_high, alert_low, shares, avg_cost)
            return jsonify({'success': True, 'message': f'已添加股票 {symbol}'})
        return jsonify({'success': False, 'message': '请提供股票代码'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/remove_stock', methods=['POST'])
def api_remove_stock():
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()
        monitor.remove_stock(symbol)
        return jsonify({'success': True, 'message': f'已移除股票 {symbol}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/update_interval', methods=['POST'])
def api_update_interval():
    global update_interval
    try:
        data = request.json
        interval = data.get('interval', 1.0)
        if 0.5 <= interval <= 30:
            update_interval = interval
            return jsonify({'success': True, 'message': f'更新间隔已设置为 {interval} 秒'})
        return jsonify({'success': False, 'message': '间隔必须在 0.5-30 秒之间'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    emit('update', get_stock_data())
    emit('welcome', {'message': '欢迎连接到美股量化分析平台'})

@socketio.on('disconnect')
def handle_disconnect():
    pass

@socketio.on('request_update')
def handle_request_update():
    emit('update', get_stock_data())

if __name__ == '__main__':
    thread = threading.Thread(target=background_monitor)
    thread.daemon = True
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)