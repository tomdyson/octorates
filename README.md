# OctoRates

OctoRates is a simple API and web application that displays Octopus Agile electricity rates, allowing users to see all upcoming slots, the cheapest slots, or the cheapest slots for tomorrow.

Live site: [https://octorates.tomd.org/](https://octorates.tomd.org/)

## Features

- View all upcoming rate slots
- Display cheapest slots (customizable number)
- Show cheapest slots for tomorrow
- API endpoints
- Caches Octopus API data

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

- GET https://octorates.tomd.org/api/all_slots
- GET https://octorates.tomd.org/api/cheapest_slots/{count}
- GET https://octorates.tomd.org/api/cheapest_slots_tomorrow/{count}
- GET https://octorates.tomd.org/api/broadcast

The `/api/broadcast` endpoint triggers a broadcast of current and upcoming prices to the configured MQTT topic.

## Technologies Used

- Backend: Python, FastAPI
- Frontend: HTML, CSS (Tachyons), JavaScript (Alpine.js)
- HTTP Client: Axios (frontend), HTTPX (backend)
- Deployment: Docker, fly.io
- CI/CD: GitHub Actions

## File Structure

- `main.py`: FastAPI backend server
- `static/index.html`: Main HTML file with Alpine.js frontend application
- `Dockerfile`: Docker configuration for deployment
- `.github/workflows/deploy.yml`: GitHub Actions workflow for CI/CD

## Notes

- The application caches Octopus API data for 10 minutes to reduce API calls
- The frontend uses Alpine.js for reactive updates and Axios for API requests
- The backend uses FastAPI for efficient API routing and HTTPX for asynchronous HTTP requests
- The app is containerized using Docker for easy deployment to fly.io
- The application is automatically deployed to fly.io when changes are pushed to the main branch
- This entire codebase was written by Claude 3.5 Sonnet

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Running Tests

To run the tests for this project, follow these steps:

1. Install the required testing dependencies:
   ```
   pip install pytest pytest-asyncio httpx
   ```

2. Run the tests using pytest:
   ```
   pytest
   ```

This will run all the tests in the `test_main.py` file and display the results.

To run tests with more detailed output, use the `-v` flag:
   ```
   pytest -v
   ```

To run a specific test function, use the `-k` flag followed by the test function name:
   ```
   pytest -v -k test_all_slots
   ```

Make sure to run the tests before deploying any changes to ensure that all functionality is working as expected.

## New Features

- MQTT Integration: Broadcasts current and upcoming prices to an MQTT topic.
- New API Endpoint: `/api/broadcast` for triggering price broadcasts.

## Environment Variables

In addition to existing environment variables, the following are used for MQTT configuration:

- `MQTT_BROKER`: The address of your MQTT broker (default: "localhost")
- `MQTT_PORT`: The port of your MQTT broker (default: 1883)
- `MQTT_TOPIC`: The topic to publish the message to (default: "octorates/prices")
- `MQTT_USERNAME`: (Optional) Username for MQTT authentication
- `MQTT_PASSWORD`: (Optional) Password for MQTT authentication

## Scheduling the Broadcast with fly.io

To call the `/api/broadcast` endpoint every 30 minutes at 00 and 30 past the hour, you can use fly.io's scheduled jobs feature. Here's how to set it up:

1. Make sure you have the latest version of the flyctl CLI installed.

2. In your project directory, create a new file named `fly.toml` if it doesn't already exist.

3. Add the following configuration to your `fly.toml` file:

   ```toml
   [scheduled_jobs]
     [scheduled_jobs.broadcast]
       schedule = "*/30 * * * *"
       command = "curl https://your-app-name.fly.dev/api/broadcast"
   ```

   Replace `your-app-name` with the actual name of your fly.io app.

4. Deploy your updated configuration:

   ```
   flyctl deploy
   ```

This configuration tells fly.io to run the curl command every 30 minutes, which will trigger your `/api/broadcast` endpoint.

Note: The free tier of fly.io may have limitations on scheduled jobs. Check the fly.io pricing and documentation for the most up-to-date information on scheduled job availability and pricing.

For more information on fly.io scheduled jobs, visit the [fly.io documentation](https://fly.io/docs/reference/scheduled-jobs/).

## Running Tests

To run the tests for this project, follow these steps:

1. Install the required testing dependencies:
   ```
   pip install pytest pytest-asyncio httpx
   ```

2. Run the tests using pytest:
   ```
   pytest
   ```

This will run all the tests in the `test_main.py` file and display the results.

To run tests with more detailed output, use the `-v` flag:
   ```
   pytest -v
   ```

To run a specific test function, use the `-k` flag followed by the test function name:
   ```
   pytest -v -k test_all_slots
   ```

Make sure to run the tests before deploying any changes to ensure that all functionality is working as expected.

## New Features

- MQTT Integration: Broadcasts current and upcoming prices to an MQTT topic.
- New API Endpoint: `/api/broadcast` for triggering price broadcasts.

## Environment Variables

In addition to existing environment variables, the following are used for MQTT configuration:

- `MQTT_BROKER`: The address of your MQTT broker (default: "localhost")
- `MQTT_PORT`: The port of your MQTT broker (default: 1883)
- `MQTT_TOPIC`: The topic to publish the message to (default: "octorates/prices")
- `MQTT_USERNAME`: (Optional) Username for MQTT authentication
- `MQTT_PASSWORD`: (Optional) Password for MQTT authentication

## Local Development with Environment Variables

For local development, this project uses a `.env` file to manage environment variables. Follow these steps to set up your local environment:

1. Create a `.env` file in the root directory of the project:
   ```
   touch .env
   ```

2. Open the `.env` file in your preferred text editor and add the following variables:
   ```
   MQTT_BROKER=your_mqtt_broker_address
   MQTT_PORT=1883
   MQTT_TOPIC=octorates/prices
   MQTT_USERNAME=your_mqtt_username
   MQTT_PASSWORD=your_mqtt_password
   ```

   Replace the values with your actual MQTT broker details.

3. Save the `.env` file.

4. The application will automatically load these environment variables when run locally, thanks to the `python-dotenv` library.

Note: The `.env` file is included in `.gitignore` to prevent sensitive information from being committed to the repository. Make sure not to accidentally commit this file.

To update your environment variables:

1. Open the `.env` file.
2. Modify the values as needed.
3. Save the file.
4. Restart your application for the changes to take effect.

Remember to update your deployment environment variables separately, as the `.env` file is only used for local development.
