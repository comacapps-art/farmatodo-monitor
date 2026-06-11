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
        return doc.to_dict().get('price_val', 0)
    return 0

def update_product_and_history(sku, product_data, current_price_val, old_price_val, now_str):
    db = get_db()
    if not db: return False
    
    # Update current price
    db.collection('products').document(sku).set({
        'price_val': current_price_val,
        'last_checked': now_str,
        'title': product_data.get('Title', ''),
        'brand': product_data.get('Brand', ''),
        'image': product_data.get('Image', ''),
        'link': product_data.get('Link', '')
    }, merge=True)
    
    # Save history
    db.collection('price_history').add({
        'sku': sku,
        'price_val': current_price_val,
        'timestamp': now_str
    })
    
    changes_found = False
    
    if old_price_val > 0 and old_price_val != current_price_val:
        diff = current_price_val - old_price_val
        direction = 'up' if diff > 0 else 'down'
        
        # Save alert
        alert_data = {
            'timestamp': now_str,
            'sku': sku,
            'title': product_data.get('Title'),
            'old_price': old_price_val,
            'new_price': current_price_val,
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
