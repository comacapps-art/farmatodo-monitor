import json
import db_manager

def migrate():
    with open('precios_db.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    db = db_manager.get_db()
    for sku, info in data.items():
        db.collection('products').document(sku).set(info)
        print(f"Migrated {sku}")

if __name__ == '__main__':
    migrate()
