import os
import pandas as pd
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from backend.services.data_processor import DataProcessor
from backend.database.models import db, Sales, FoodItem
import os
from pathlib import Path

# This gets the 'food-forecasting-system' root folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent

data_bp = Blueprint('data', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
BATCH_SIZE = 1000  # Upload in chunks to avoid timeouts

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@data_bp.route('/upload', methods=['POST'])
def upload_data():
    """Upload Kaggle Food Demand data to Neon DB"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    # Use center_id from form or default to 1
    default_outlet_id = request.form.get('outlet_id', 1)

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use CSV or Excel'}), 400

    try:
        # 1. Save and Process File
        filename = secure_filename(file.filename)
        os.makedirs('data/raw', exist_ok=True)
        filepath = os.path.join(BASE_DIR, 'data', 'raw', filename)
        file.save(filepath)

        processor = DataProcessor()
        processor.load_data(filepath, limit=50)
        processor.clean_data()
        processor.feature_engineering()

        # 2. Batch Upload Logic
        records_added = 0
        start_date = datetime.now().date()

        for i, row in processor.df.iterrows():
            # Get or Create Food Item (using meal_id)
            meal_id = int(row['meal_id'])
            food_item = FoodItem.query.get(meal_id)
            
            if not food_item:
                food_item = FoodItem(
                    id=meal_id,
                    name=f"Meal {meal_id}",
                    category="General"
                )
                db.session.add(food_item)
                db.session.flush() # Get ID before committing

            # Create Sales Record (Mapping Kaggle -> DB)
            # Kaggle 'week' is turned into an actual date for the DB
            sale_date = start_date + timedelta(weeks=int(row['week']))
            
            sale = Sales(
                outlet_id=int(row.get('center_id', default_outlet_id)),
                food_item_id=food_item.id,
                date=sale_date,
                quantity_sold=int(row['num_orders']),
                revenue=float(row['checkout_price']) * int(row['num_orders'])
            )
            db.session.add(sale)
            records_added += 1

            # Commit in batches to prevent memory/timeout issues
            if records_added % BATCH_SIZE == 0:
                db.session.commit()

        db.session.commit() # Final commit for remaining rows

        # 3. Save Cleaned Version
        os.makedirs('data/processed', exist_ok=True)
        processed_path = f'data/processed/processed_{filename}'
        processor.save_processed_data(processed_path)

        return jsonify({
            'status': 'success',
            'records_added': records_added,
            'message': f'Successfully uploaded {records_added} records to Neon'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@data_bp.route('/validate', methods=['POST'])
def validate_data():
    """Validate Kaggle columns without saving"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    try:
        df = pd.read_csv(file)
        
        # The actual Kaggle columns we need
        required_cols = ['week', 'center_id', 'meal_id', 'num_orders', 'checkout_price']
        missing_cols = [col for col in required_cols if col not in df.columns]

        return jsonify({
            'valid': len(missing_cols) == 0,
            'rows': len(df),
            'missing_columns': missing_cols,
            'sample': df.head(3).to_dict(orient='records')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500