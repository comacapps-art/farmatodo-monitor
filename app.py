from flask import Flask, render_template, request, jsonify, send_file
import os
import scraper

app = Flask(__name__)
OUTPUT_FILE = 'products.csv'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'La búsqueda no puede estar vacía'}), 400
        
    try:
        # Fetch BCV rate
        bcv_rate = 0.0
        try:
            import requests
            res = requests.get('https://ve.dolarapi.com/v1/dolares/oficial', timeout=5)
            if res.status_code == 200:
                bcv_rate = float(res.json().get('promedio', 0))
        except:
            pass
            
        # Run the scraper in headless mode for the server
        products, output_file = scraper.scrape_farmatodo(url, headless=True)
        
        # Add USD price to products
        for p in products:
            try:
                import re
                price_str = str(p.get('Price', ''))
                digits = re.sub(r'[^\d]', '', price_str)
                if digits and bcv_rate > 0:
                    price_bs = float(digits) / 100.0
                    p['Price_USD'] = round(price_bs / bcv_rate, 2)
                else:
                    p['Price_USD'] = 0
            except:
                p['Price_USD'] = 0
            p['BCV_Rate'] = bcv_rate
            
        return jsonify({
            'message': 'Scraping completado', 
            'products': products,
            'download_file': output_file,
            'bcv_rate': bcv_rate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    file_name = request.args.get('file')
    if not file_name or not os.path.exists(file_name):
        return "Archivo no encontrado", 404
        
    try:
        return send_file(file_name, as_attachment=True)
    except Exception as e:
        return str(e)

import monitor

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    data = request.json
    query = data.get('query')
    # Default 1 minute interval for testing, normally 3600
    interval = data.get('interval', 60) 
    
    if not query:
        return jsonify({'error': 'Falta la búsqueda'}), 400
        
    monitor.start_monitoring(query, interval=interval)
    return jsonify({'status': 'Monitoring started', 'query': query})

@app.route('/api/stop_monitor', methods=['POST'])
def stop_monitor():
    monitor.stop_monitoring()
    return jsonify({'status': 'Monitoring stopped'})

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    try:
        return jsonify({
            'alerts': monitor.get_alerts(),
            'status': monitor.get_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

import db_manager

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        return jsonify({
            'history': db_manager.get_all_history()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    try:
        return jsonify({
            'watchlist': db_manager.get_watchlist()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist/add', methods=['POST'])
def add_watchlist():
    data = request.json
    term = data.get('term')
    if not term:
        return jsonify({'error': 'Falta el término'}), 400
    db_manager.add_watchlist_item(term)
    return jsonify({'status': 'ok'})

@app.route('/api/watchlist/remove', methods=['POST'])
def remove_watchlist():
    data = request.json
    doc_id = data.get('id')
    if not doc_id:
        return jsonify({'error': 'Falta el ID'}), 400
    db_manager.remove_watchlist_item(doc_id)
    return jsonify({'status': 'ok'})

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        return jsonify({
            'dashboard': db_manager.get_dashboard_data()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

import os
if __name__ == '__main__':
    # Run the server on Render's assigned port or 5000 locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
