# OctoRates

OctoRates is a web application that displays Octopus Agile electricity rates, allowing users to view all upcoming slots, the cheapest slots, or the cheapest slots for tomorrow.

## Features

- View all upcoming rate slots
- Display cheapest slots (customizable number)
- Show cheapest slots for tomorrow
- API endpoints information
- Caching of Octopus API data

## Prerequisites

- Python 3.x
- FastAPI
- HTTPX
- Docker (for deployment)
- fly.io CLI (for deployment)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/octorates.git
   cd octorates
   ```

2. Install dependencies:
   ```
   pip install fastapi uvicorn httpx
   ```

## Running the Application Locally

1. Start the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

2. Open a web browser and navigate to `http://localhost:8000`

## Deployment to fly.io

1. Install the fly.io CLI following the instructions at https://fly.io/docs/hands-on/install-flyctl/

2. Log in to your fly.io account:
   ```
   flyctl auth login
   ```

3. Initialize your fly.io app:
   ```
   flyctl launch
   ```
   This will create a `fly.toml` file in your project directory.

4. Deploy your app:
   ```
   flyctl deploy
   ```

5. Once deployed, you can open your app in the browser:
   ```
   flyctl open
   ```

## API Endpoints

- GET /api/all_slots
- GET /api/cheapest_slots/{count}
- GET /api/cheapest_slots_tomorrow/{count}

## Technologies Used

- Backend: Python, FastAPI
- Frontend: HTML, CSS (Tachyons), JavaScript (Vue.js)
- HTTP Client: Axios (frontend), HTTPX (backend)
- Deployment: Docker, fly.io

## File Structure

- `main.py`: FastAPI backend server
- `static/index.html`: Main HTML file
- `static/app.js`: Vue.js frontend application
- `Dockerfile`: Docker configuration for deployment

## Notes

- The application caches Octopus API data for 10 minutes to reduce API calls
- The frontend uses Vue.js for reactive updates and Axios for API requests
- The backend uses FastAPI for efficient API routing and HTTPX for asynchronous HTTP requests
- The app is containerized using Docker for easy deployment to fly.io

## License

[Your chosen license]