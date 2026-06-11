import time
import threading
import json
import os
import datetime
from scraper import scrape_farmatodo
import db_manager

is_monitoring = False
monitor_thread = None
current_query = None
check_interval = 3600  # 1 hour by default, will reduce to 60s for testing if needed

def _monitor_loop():
    global is_monitoring, current_query
    
    while is_monitoring:
        if not current_query:
            time.sleep(10)
            continue
            
        print(f"[Monitor] Iniciando revisión de precios para: {current_query}")
        
        try:
            # We run the scraper in a separate process because Playwright crashes inside Flask background threads
            import subprocess
            import sys
            cmd = [
                sys.executable, "-c",
                f"import json; from scraper import scrape_farmatodo; data, _ = scrape_farmatodo('{current_query}', headless=True); "
                "open('monitor_temp.json', 'w', encoding='utf-8').write(json.dumps(data))"
            ]
            
            subprocess.run(cmd, check=True)
            
            with open('monitor_temp.json', 'r', encoding='utf-8') as f:
                products = json.load(f)
                
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for p in products:
                sku = p.get('SKU') or p.get('Title')
                price_str = str(p.get('Price', ''))
                
                try:
                    import re
                    digits = re.sub(r'[^\d]', '', price_str)
                    if not digits: continue
                    current_price_val = float(digits) / 100.0
                except:
                    continue
                    
                old_price_val = db_manager.get_product_price(sku)
                
                changed = db_manager.update_product_and_history(
                    sku, p, current_price_val, old_price_val, now_str
                )
                
                if changed:
                    print(f"[ALERTA] Cambio detectado en {sku}: {old_price_val} -> {current_price_val}")
                
        except Exception as e:
            print(f"[Monitor] Error: {e}")
            
        # Sleep for check_interval seconds
        for _ in range(check_interval):
            if not is_monitoring:
                break
            time.sleep(1)

def start_monitoring(query, interval=3600):
    global is_monitoring, monitor_thread, current_query, check_interval
    current_query = query
    check_interval = interval
    
    if not is_monitoring:
        is_monitoring = True
        monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
        monitor_thread.start()
        return True
    return False

def stop_monitoring():
    global is_monitoring
    is_monitoring = False

def get_alerts():
    return db_manager.get_alerts()

def get_status():
    return {
        "is_monitoring": is_monitoring,
        "query": current_query,
        "interval": check_interval
    }
