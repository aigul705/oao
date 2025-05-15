# Precious Metals Price Tracker

A web application for tracking precious metals prices using Alpha Vantage API, built with Flask backend and TypeScript frontend.

## Project Structure

- `backend/` - Flask backend application
  - `app/` - Application code
  - `venv/` - Python virtual environment (created during setup)
  - `.env` - Environment variables (created during setup)
  - `app.db` - SQLite database (created during setup)
- `frontend/` - TypeScript frontend application

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Unix/MacOS
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

5. Run the Flask application:
   ```bash
   python run.py
   ```

The backend will be available at: http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at: http://localhost:5173

## API Endpoints

### Current Prices
- `GET /api/metals/current`
  - Returns current prices for all metals
  - Example response:
    ```json
    {
      "status": "success",
      "data": [
        {
          "symbol": "GOLD",
          "name": "Gold",
          "price": 1945.30,
          "unit": "USD/oz",
          "timestamp": "2024-01-20"
        }
      ]
    }
    ```

### Historical Prices
- `GET /api/metals/history?metal=GOLD&date_from=2024-01-01&date_to=2024-01-20`
  - Returns historical prices for a specific metal
  - Required parameters:
    - `metal`: Metal symbol (GOLD, SILVER, PLATINUM, PALLADIUM)
    - `date_from`: Start date (YYYY-MM-DD)
    - `date_to`: End date (YYYY-MM-DD)

### Price Analysis
- `GET /api/metals/analysis?metal=GOLD`
  - Returns analysis for a specific metal
  - Required parameters:
    - `metal`: Metal symbol (GOLD, SILVER, PLATINUM, PALLADIUM)

## Features

- Real-time price updates every 10 minutes
- Historical price data
- Price trend analysis
- Volatility calculation
- Market sentiment analysis
- Caching to respect API rate limits

## Development

- Backend runs on: http://localhost:5000
- Frontend runs on: http://localhost:5173
- Database: SQLite (app.db in backend directory)
- API Key: Alpha Vantage (configured in .env)

## Technologies Used

### Backend
- Flask
- Flask-CORS
- Flask-SQLAlchemy
- Flask-Caching
- Alpha Vantage API
- SQLite

### Frontend
- TypeScript
- React
- Vite
- Axios
- TailwindCSS 