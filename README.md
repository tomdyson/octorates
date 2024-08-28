# OctoRates

OctoRates is a web application that displays Octopus Agile electricity rates, allowing users to view all upcoming slots, the cheapest slots, or the cheapest slots for tomorrow.

Live site: [https://octorates.fly.dev/](https://octorates.fly.dev/)

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
   git clone https://github.com/tomdyson/octorates.git
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

## Continuous Integration (CI)

This project uses GitHub Actions for continuous integration and deployment. When changes are pushed to the main branch, the application is automatically deployed to fly.io.

The CI/CD pipeline is configured in `.github/workflows/deploy.yml` and includes the following steps:

1. Checkout the code
2. Set up the fly.io CLI
3. Verify the existence of the `fly.toml` file
4. Deploy to fly.io

To set up CI/CD for your fork of this project:

1. Fork this repository
2. Set up a fly.io account and install the fly.io CLI
3. Create a fly.io app for your project
4. Add your `FLY_API_TOKEN` as a secret in your GitHub repository settings
5. Push changes to the main branch to trigger a deployment

## API Endpoints

- GET /api/all_slots
- GET /api/cheapest_slots/{count}
- GET /api/cheapest_slots_tomorrow/{count}

## Technologies Used

- Backend: Python, FastAPI
- Frontend: HTML, CSS (Tachyons), JavaScript (Vue.js)
- HTTP Client: Axios (frontend), HTTPX (backend)
- Deployment: Docker, fly.io
- CI/CD: GitHub Actions

## File Structure

- `main.py`: FastAPI backend server
- `static/index.html`: Main HTML file
- `static/app.js`: Vue.js frontend application
- `Dockerfile`: Docker configuration for deployment
- `.github/workflows/deploy.yml`: GitHub Actions workflow for CI/CD

## Notes

- The application caches Octopus API data for 10 minutes to reduce API calls
- The frontend uses Vue.js for reactive updates and Axios for API requests
- The backend uses FastAPI for efficient API routing and HTTPX for asynchronous HTTP requests
- The app is containerized using Docker for easy deployment to fly.io
- The application is automatically deployed to fly.io when changes are pushed to the main branch

## License

[Your chosen license]