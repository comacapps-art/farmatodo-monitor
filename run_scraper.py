import os
import json
import datetime
import subprocess
import sys
import db_manager

def run_single_scrape():
    # En GitHub Actions, leemos la consulta de una variable de entorno, por defecto 'NOVEX'
    query = os.environ.get('MONITOR_QUERY', 'NOVEX')
    print(f"[Scraper] Iniciando extracción en la nube para: {query}")
    
    # Run scraper in a subprocess
    cmd = [
        sys.executable, "-c",
        f"import json; from scraper import scrape_farmatodo; data, _ = scrape_farmatodo('{query}', headless=True); "
        "open('monitor_temp.json', 'w', encoding='utf-8').write(json.dumps(data))"
    ]
    subprocess.run(cmd, check=True)
    
    with open('monitor_temp.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
        
    print(f"[Scraper] {len(products)} productos extraídos.")
    
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    changes_count = 0
    
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
            
    print(f"[Scraper] Proceso finalizado. {changes_count} alertas generadas.")

if __name__ == "__main__":
    run_single_scrape()
