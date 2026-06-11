import os
import json
import datetime
import subprocess
import sys
import db_manager

def run_single_scrape():
    watchlist = db_manager.get_watchlist()
    
    if not watchlist:
        print("[Scraper] La watchlist está vacía. Terminando.")
        return
        
    changes_count = 0
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for item in watchlist:
        query = item.get('term')
        print(f"\\n[Scraper] Iniciando extracción para: {query}")
        
        try:
            cmd = [
                sys.executable, "-c",
                f"import json; from scraper import scrape_farmatodo; data, _ = scrape_farmatodo('{query}', headless=True); "
                "open('monitor_temp.json', 'w', encoding='utf-8').write(json.dumps(data))"
            ]
            subprocess.run(cmd, check=True)
            
            with open('monitor_temp.json', 'r', encoding='utf-8') as f:
                products = json.load(f)
                
            print(f"[Scraper] {len(products)} productos extraídos para {query}.")
            
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
                    changes_count += 1
        except Exception as e:
            print(f"Error procesando {query}: {e}")
            
    print(f"\\n[Scraper] Proceso finalizado. {changes_count} alertas generadas en total.")

if __name__ == "__main__":
    run_single_scrape()
