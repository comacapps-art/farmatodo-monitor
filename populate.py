import json

data = json.load(open('monitor_temp.json', 'r', encoding='utf-8'))
db = {}

for p in data:
    try:
        import re
        price_str = str(p.get('Price', ''))
        digits = re.sub(r'[^\d]', '', price_str)
        if not digits: continue
        val_str = float(digits) / 100.0
        db[p.get('SKU')] = {
            'price_val': val_str,
            'last_checked': '2026-06-10 17:00:00',
            'title': p.get('Title')
        }
    except:
        pass

open('precios_db.json', 'w', encoding='utf-8').write(json.dumps(db, indent=4))
