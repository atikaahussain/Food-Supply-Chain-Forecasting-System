import os
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from backend.services.data_processor import DataProcessor
from backend.database.models import db, Sales, FoodItem, Outlet
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
data_bp = Blueprint('data', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
# Increase BATCH_SIZE for bulk execution
BATCH_SIZE = 5000 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_bp.route('/upload', methods=['POST'])
def upload_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    try:
        filename = secure_filename(file.filename)
        os.makedirs('data/raw', exist_ok=True)
        filepath = os.path.join(BASE_DIR, 'data', 'raw', filename)
        file.save(filepath)

        processor = DataProcessor()
        processor.load_data(filepath)
        processor.clean_data()
        processor.feature_engineering()

        # Check if this is the frontend format (date, customer_count, food_item, quantity_sold, revenue)
        # or the original format (center_id, meal_id, week, num_orders, checkout_price)
        df = processor.df
        
        if 'date' in df.columns and 'customer_count' in df.columns:
            # Frontend format
            print("📁 Detected frontend upload format")
            
            # Validate required columns
            required_cols = ['date', 'customer_count', 'food_item', 'quantity_sold']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return jsonify({'error': f'Missing required columns: {missing_cols}'}), 400
            
            # Get outlet_id from request or default to 1
            outlet_id = request.form.get('outlet_id', 1, type=int)
            
            # Pre-cache food items
            unique_items = df['food_item'].unique()
            for item_name in unique_items:
                if not FoodItem.query.filter_by(name=str(item_name)).first():
                    db.session.add(FoodItem(name=str(item_name), category="General"))
            
            # Ensure outlet exists
            if not Outlet.query.get(outlet_id):
                db.session.add(Outlet(id=outlet_id, name=f"Outlet {outlet_id}", location="Unknown"))
            
            db.session.commit()
            
            # Bulk insert sales
            records_added = 0
            sales_buffer = []
            
            for i, row in df.iterrows():
                try:
                    sale_entry = {
                        "outlet_id": outlet_id,
                        "food_item_id": FoodItem.query.filter_by(name=str(row['food_item'])).first().id,
                        "date": pd.to_datetime(row['date']).date(),
                        "customer_count": int(row.get('customer_count', 0)) if not pd.isna(row.get('customer_count')) else 0,
                        "quantity_sold": int(row['quantity_sold']),
                        "revenue": float(row.get('revenue', 0)) if not pd.isna(row.get('revenue')) else 0.0
                    }
                    sales_buffer.append(sale_entry)
                    records_added += 1
                    
                    if len(sales_buffer) >= BATCH_SIZE:
                        db.session.execute(db.insert(Sales), sales_buffer)
                        db.session.commit()
                        sales_buffer = []
                        
                except Exception as row_error:
                    print(f"⚠️ Skipping row {i}: {row_error}")
                    continue
            
            # Final commit
            if sales_buffer:
                db.session.execute(db.insert(Sales), sales_buffer)
                db.session.commit()
                
        else:
            # Original format (center_id, meal_id, week, num_orders, checkout_price)
            print("📁 Detected original dataset format")
            
            # --- TURBO STEP 1: PRE-CACHE OUTLETS AND MEALS ---
            unique_centers = df['center_id'].unique()
            unique_meals = df['meal_id'].unique()

            for c_id in unique_centers:
                if not Outlet.query.get(int(c_id)):
                    db.session.add(Outlet(id=int(c_id), name=f"Center {c_id}", location="Unknown"))
            
            for m_id in unique_meals:
                if not FoodItem.query.get(int(m_id)):
                    db.session.add(FoodItem(id=int(m_id), name=f"Meal {m_id}", category="General"))
            
            db.session.commit()
            print("✅ Pre-caching complete. Starting bulk sales upload...")

            # --- TURBO STEP 2: BULK INSERT SALES ---
            records_added = 0
            start_date = datetime.now().date() - timedelta(weeks=150)
            sales_buffer = []

            for i, row in df.iterrows():
                sale_date = start_date + timedelta(weeks=int(row['week']))
                
                sale_entry = {
                    "outlet_id": int(row['center_id']),
                    "food_item_id": int(row['meal_id']),
                    "date": sale_date,
                    "customer_count": int(row.get('customer_count', 0)) if not pd.isna(row.get('customer_count')) else 0,
                    "quantity_sold": int(row['num_orders']),
                    "revenue": float(row['checkout_price']) * int(row['num_orders'])
                }
                sales_buffer.append(sale_entry)
                records_added += 1

                if len(sales_buffer) >= BATCH_SIZE:
                    db.session.execute(db.insert(Sales), sales_buffer)
                    db.session.commit()
                    sales_buffer = []
                    print(f"🚀 Uploaded {records_added} records...")

            # Final commit for remaining rows
            if sales_buffer:
                db.session.execute(db.insert(Sales), sales_buffer)
                db.session.commit()

        return jsonify({
            'status': 'success',
            'records_added': records_added,
            'message': f'Successfully uploaded {records_added} records'
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@data_bp.route('/stats', methods=['GET'])
def get_data_stats():
    """
    Return high-level database statistics for the dashboard.

    GET /api/data/stats
    Response: {
        "total_records": 12345,
        "total_food_items": 8,
        "total_outlets": 3,
        "date_range": {"min": "2023-01-01", "max": "2024-12-31"},
        "has_data": true
    }
    """
    try:
        from sqlalchemy import func

        total_records = db.session.query(func.count(Sales.id)).scalar() or 0
        total_food_items = db.session.query(func.count(FoodItem.id)).scalar() or 0
        total_outlets = db.session.query(func.count(Outlet.id)).scalar() or 0

        min_date = db.session.query(func.min(Sales.date)).scalar()
        max_date = db.session.query(func.max(Sales.date)).scalar()

        # Find the first outlet ID that actually has data
        suggested_outlet = db.session.query(Sales.outlet_id).first()
        suggested_outlet_id = suggested_outlet[0] if suggested_outlet else 1

        return jsonify({
            'total_records': total_records,
            'total_food_items': total_food_items,
            'total_outlets': total_outlets,
            'date_range': {
                'min': min_date.isoformat() if min_date else None,
                'max': max_date.isoformat() if max_date else None,
            },
            'has_data': total_records > 0,
            'suggested_outlet_id': suggested_outlet_id
        }), 200

    except Exception as e:
        print(f"❌ Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500