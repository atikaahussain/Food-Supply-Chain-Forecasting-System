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
            
            # Load meal info for better naming if available
            meal_names = {}
            meal_info_path = os.path.join(BASE_DIR, 'data', 'raw', 'meal_info.csv')
            if os.path.exists(meal_info_path):
                try:
                    meal_info_df = pd.read_csv(meal_info_path)
                    for _, m_row in meal_info_df.iterrows():
                        meal_names[int(m_row['meal_id'])] = f"{m_row['cuisine']} {m_row['category']}"
                except Exception as e:
                    print(f"⚠️ Could not load meal_info.csv: {e}")

            unique_centers = df['center_id'].unique()
            unique_meals = df['meal_id'].unique()

            for c_id in unique_centers:
                if not Outlet.query.get(int(c_id)):
                    db.session.add(Outlet(id=int(c_id), name=f"Center {c_id}", location="Unknown"))
            
            for m_id in unique_meals:
                if not FoodItem.query.get(int(m_id)):
                    name = meal_names.get(int(m_id), f"Meal {m_id}")
                    db.session.add(FoodItem(id=int(m_id), name=name, category="General"))
            
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
                
                # Update FoodItem unit price if not set or if we want latest
                food_item = FoodItem.query.get(int(row['meal_id']))
                if food_item and (not food_item.unit_price or food_item.unit_price == 0):
                    food_item.unit_price = float(row['checkout_price'])
                
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


@data_bp.route('/fix-names', methods=['POST'])
def fix_meal_names():
    """
    Utility route to fix existing 'Meal XXXX' names in the database
    using meal_info.csv mapping.
    """
    try:
        meal_names = {}
        meal_info_path = os.path.join(BASE_DIR, 'data', 'raw', 'meal_info.csv')
        if not os.path.exists(meal_info_path):
            return jsonify({'error': 'meal_info.csv not found in data/raw/'}), 404
            
        meal_info_df = pd.read_csv(meal_info_path)
        for _, m_row in meal_info_df.iterrows():
            meal_names[int(m_row['meal_id'])] = f"{m_row['cuisine']} {m_row['category']}"
        
        items_fixed = 0
        all_items = FoodItem.query.all()
        for item in all_items:
            name_str = str(item.name)
            if name_str.startswith('Meal ') or name_str.isdigit():
                meal_id = None
                if name_str.startswith('Meal '):
                    try:
                        meal_id = int(name_str.replace('Meal ', ''))
                    except: pass
                else:
                    try:
                        meal_id = int(item.id)
                    except: pass
                
                if meal_id in meal_names:
                    item.name = meal_names[meal_id]
                    items_fixed += 1
            
            # Fix zero prices if possible
            if not item.unit_price or item.unit_price == 0:
                latest_sale = Sales.query.filter_by(food_item_id=item.id).order_by(Sales.date.desc()).first()
                if latest_sale:
                    # Calculate unit price from revenue and quantity
                    if latest_sale.quantity_sold > 0:
                        item.unit_price = latest_sale.revenue / latest_sale.quantity_sold
                    elif latest_sale.revenue > 0:
                        item.unit_price = latest_sale.revenue
        
        db.session.commit()
        return jsonify({
            'status': 'success',
            'items_fixed': items_fixed,
            'message': f'Successfully updated {items_fixed} meal names'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Fix names error: {str(e)}")
        return jsonify({'error': str(e)}), 500