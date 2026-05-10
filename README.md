# Food Demand Forecasting & Inventory Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791.svg)](https://neon.tech/)

A sophisticated full-stack AI solution designed to revolutionize restaurant operations. By predicting customer demand with high-precision machine learning models, the system automatically generates optimized ingredient shopping lists, minimizing food waste and maximizing operational efficiency.

---

## Technical Stack

Our system is built using a modern, scalable architecture designed for performance and reliability.

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React.js, Material UI (MUI 5), Recharts, React-Router |
| **Backend** | Flask (Python), SQLAlchemy ORM, JWT Authentication, Flask-CORS |
| **AI / ML** | LinearRegression,ARIMA,XGBoost,LSTM, Scikit-learn, Pandas, NumPy |
| **Database** | Neon PostgreSQL (Serverless Cloud Database) |
| **Reporting** | ReportLab (PDF), XlsxWriter (Excel) |

---

## Key Features

- **AI-Powered Forecasting**: Supports multiple models (XGBoost, Linear Regression) with an "Auto-Select" logic that automatically chooses the most accurate algorithm for your specific data.
- **Bulk Data Ingestion**: Robust CSV processing engine capable of handling large Kaggle datasets (processed in high-speed batches of 5,000+ records).
- **Automated Inventory**: Sophisticated recipe-engine that translates AI customer predictions into precise raw ingredient requirements.
- **Smart Alerts**: Proactive shortage detection that warns kitchen managers before ingredients run out, based on predicted surges in demand.
- **Responsive Dashboard**: A premium, "glassmorphic" user interface that works seamlessly on Desktop, Tablet, and Mobile devices.

---

## System Architecture

The system follows a decoupled client-server architecture to ensure modularity and ease of maintenance:

1.  **Frontend**: The React application handles user interactions, data visualization, and CSV file selection.
2.  **API Layer**: Flask serves as the central hub, processing requests, managing authentication, and handling business logic.
3.  **Data Layer**: Neon Cloud PostgreSQL stores sales history, ingredient recipes, and system metadata.
4.  **AI Engine**: A dedicated service that fetches historical data, trains models on-the-fly (or uses pre-trained weights), and outputs demand predictions.
5.  **Inventory Logic**: Processes demand forecasts through a recipe-mapping service to calculate procurement needs.

---

## Installation & Setup

### Step 1: Clone & Backend Setup
```bash
# Clone the repository
git clone [your-repo-link]
cd food-forecasting-system

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Variables
Create a `.env` file in the `backend/` directory:
```plaintext
DATABASE_URL=your_neon_db_url_here
SECRET_KEY=your_secure_random_secret_key
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm start
```

---

## Using the Kaggle Dataset

To populate the system with real-world data:
1.  Download the **Food Demand Forecasting** dataset from Kaggle (e.g., `train.csv`).
2.  Navigate to the **"Upload Data"** tab in the dashboard.
3.  Upload the CSV file. The system will automatically reconcile meal names and process historical trends.
4.  Once uploaded, head to the **"Dashboard"** to generate your first AI forecast!


---


*Developed as part of the Advanced Food Supply Chain Forecasting Project.*
