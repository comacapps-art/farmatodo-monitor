import firebase_admin
from firebase_admin import credentials, firestore
import os
import time

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
        
    cred_path = "firebase_credentials.json"
    if not os.path.exists(cred_path):
        print("Esperando firebase_credentials.json...")
        return None
        
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        
    _db = firestore.client()
    return _db

def get_product_price(sku):
    db = get_db()
    if not db: return 0
    doc = db.collection('products').document(sku).get()
    if doc.exists:
def get_product_info(sku):
    db = get_db()
    if not db: return {'price_val': 0, 'price_usd': 0, 'last_checked': ''}
    doc = db.collection('products').document(sku).get()
    if doc.exists:
        data = doc.to_dict()
        return {
            'price_val': data.get('price_val', 0),
            'price_usd': data.get('price_usd', 0),
            'last_checked': data.get('last_checked', '')
        }
    return {'price_val': 0, 'price_usd': 0, 'last_checked': ''}

def update_product_and_history(sku, product_data, current_price_bs, current_price_usd, old_price_usd, old_timestamp, bcv_rate, now_str):
    db = get_db()
    if not db: return False
    
    # Update current price
    db.collection('products').document(sku).set({
        'price_val': current_price_bs,
        'price_usd': current_price_usd,
        'old_price_usd': old_price_usd,
        'old_timestamp': old_timestamp,
        'bcv_rate': bcv_rate,
        'last_checked': now_str,
        'title': product_data.get('Title', ''),
        'brand': product_data.get('Brand', ''),
        'image': product_data.get('Image', ''),
        'link': product_data.get('Link', '')
    }, merge=True)
    
    # Save history
    db.collection('price_history').add({
        'sku': sku,
        'title': product_data.get('Title', ''),
        'brand': product_data.get('Brand', ''),
        'price_val': current_price_bs,
        'price_usd': current_price_usd,
        'bcv_rate': bcv_rate,
        'timestamp': now_str
    })
    
    changes_found = False
    
    # Solo alertar si el precio viejo en USD existe y es diferente al actual
    if old_price_usd > 0 and old_price_usd != current_price_usd:
        diff = current_price_usd - old_price_usd
        direction = 'up' if diff > 0 else 'down'
        
        # Save alert
        alert_data = {
            'timestamp': now_str,
            'old_timestamp': old_timestamp,
            'sku': sku,
            'title': product_data.get('Title'),
            'old_price': old_price_usd,
            'new_price': current_price_usd,
            'bcv_rate': bcv_rate,
            'direction': direction,
            'image': product_data.get('Image')
        }
        db.collection('alerts').add(alert_data)
        changes_found = True
        
    return changes_found

def get_alerts(limit=20):
    db = get_db()
    if not db: return []
    
    alerts_ref = db.collection('alerts').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
    docs = alerts_ref.stream()
    
    alerts = []
    for doc in docs:
        alerts.append(doc.to_dict())
    return alerts

def get_all_history():
    db = get_db()
    if not db: return []
    
    docs = db.collection('price_history').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    history = []
    for doc in docs:
        history.append(doc.to_dict())
    return history

def get_watchlist():
    db = get_db()
    if not db: return []
    
    docs = db.collection('watchlist').order_by('added_at', direction=firestore.Query.DESCENDING).stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        items.append(data)
    return items

def add_watchlist_item(term):
    db = get_db()
    if not db: return False
    
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')
    db.collection('watchlist').add({
        'term': term,
        'added_at': now_str
    })
    return True

def remove_watchlist_item(doc_id):
    db = get_db()
    if not db: return False
    
    db.collection('watchlist').document(doc_id).delete()
    return True

def get_dashboard_data():
    db = get_db()
    if not db: return []
    
    # Obtener todos los productos vigilados
    docs = db.collection('products').order_by('last_checked', direction=firestore.Query.DESCENDING).stream()
    dashboard = []
    for doc in docs:
        data = doc.to_dict()
        data['sku'] = doc.id
        dashboard.append(data)
    return dashboard

def save_daily_rate(date_str, rate_val):
    db = get_db()
    if not db: return False
    db.collection('exchange_rates').document(date_str).set({
        'rate': rate_val,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    return True

def get_rate_history():
    db = get_db()
    if not db: return []
    docs = db.collection('exchange_rates').order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    rates = []
    for doc in docs:
        rates.append({
            'date': doc.id,
            'rate': doc.to_dict().get('rate', 0)
        })
    return rates

def get_current_bcv_rate():
    # 1. Check if there's a manual rate for today
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    db = get_db()
    if db:
        doc = db.collection('exchange_rates').document(today_str).get()
        if doc.exists:
            return float(doc.to_dict().get('rate', 0)), 'manual'
            
    # 2. If not, fetch from API
    try:
        import requests
        res = requests.get('https://ve.dolarapi.com/v1/dolares/oficial', timeout=10)
        if res.status_code == 200:
            return float(res.json().get('promedio', 0)), 'api'
    except:
        pass
        
    return 0, 'error'
