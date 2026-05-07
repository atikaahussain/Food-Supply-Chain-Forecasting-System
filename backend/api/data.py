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

        # --- TURBO STEP 1: PRE-CACHE OUTLETS AND MEALS ---
        # Get all unique IDs from the CSV to avoid checking inside the loop
        unique_centers = processor.df['center_id'].unique()
        unique_meals = processor.df['meal_id'].unique()

        for c_id in unique_centers:
            if not Outlet.query.get(int(c_id)):
                db.session.add(Outlet(id=int(c_id), name=f"Center {c_id}", location="Unknown"))
        
        for m_id in unique_meals:
            if not FoodItem.query.get(int(m_id)):
                db.session.add(FoodItem(id=int(m_id), name=f"Meal {m_id}", category="General"))
        
        db.session.commit() # Save all parents at once
        print("✅ Pre-caching complete. Starting bulk sales upload...")

        # --- TURBO STEP 2: BULK INSERT SALES ---
        records_added = 0
        start_date = datetime.now().date() - timedelta(weeks=150)
        sales_buffer = []

        for i, row in processor.df.iterrows():
            sale_date = start_date + timedelta(weeks=int(row['week']))
            
            # Prepare data as a simple dictionary instead of a Model object
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

            # Execute bulk insert every BATCH_SIZE
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
            'message': f'Turbo Uploaded {records_added} records'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500