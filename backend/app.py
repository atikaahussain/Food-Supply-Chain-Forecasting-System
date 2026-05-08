import sys
from pathlib import Path
from flask import Flask
from flask_cors import CORS

# 1. Path fix: Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# 2. Import directly from submodules to avoid __init__.py indirection issues
from backend.configfile import Config
from backend.database.models import db
from backend.api.data import data_bp
from backend.api.forecast import forecast_bp
from backend.api.inventory import inventory_bp
from backend.api.reports import reports_bp
from backend.api.auth import auth_bp
from backend.services.scheduler import ForecastScheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # 3. Enable CORS for React frontend (Port 3000/3001)
    CORS(app,
         origins=["http://localhost:3000", "http://localhost:3001",
                  "http://192.168.100.118:3000", "http://192.168.100.118:3001"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=True)

    # 4. Register blueprints
    app.register_blueprint(data_bp,      url_prefix='/api/data')
    app.register_blueprint(forecast_bp,  url_prefix='/api/forecast')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(reports_bp,   url_prefix='/api/reports')
    app.register_blueprint(auth_bp,      url_prefix='/api/auth')

    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB
    app.config['JSON_SORT_KEYS'] = False

    # Debug: print routes on startup
    with app.app_context():
        print("\n--- REGISTERED ROUTES ---")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint:40s} -> {rule}")
        print("--------------------------\n")

    scheduler = ForecastScheduler(app)
    scheduler.start()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')