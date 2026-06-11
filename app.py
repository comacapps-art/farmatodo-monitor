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
        # Run the scraper in headless mode for the server
        products, output_file = scraper.scrape_farmatodo(url, headless=True)
        return jsonify({
            'message': 'Scraping completado', 
            'products': products,
            'download_file': output_file
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

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000)
