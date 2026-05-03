import sys
from pathlib import Path

# Allow `python backend/app.py` to work by ensuring repo root
# is on sys.path (so `import backend.*` resolves correctly).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from flask import Flask
from flask_cors import CORS
from backend.configfile import Config
from backend.database.models import db
from backend.api import data_bp  # Import from the API package
from backend.api.forecast import forecast_bp
from backend.services.scheduler import ForecastScheduler

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    CORS(app)
    
    # Register blueprint
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
    
    # Debug: Print routes to Terminal 1 to confirm it worked
    with app.app_context():
        print("\n--- REGISTERED ROUTES ---")
        for rule in app.url_map.iter_rules():
            print(f"Endpoint: {rule.endpoint} -> {rule}")
        print("--------------------------\n")
        
    scheduler = ForecastScheduler(app)
    scheduler.start()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)