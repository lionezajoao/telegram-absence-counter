# Telegram Absence Counter Bot

A Telegram bot designed to help university students easily track and manage their class absences.

## Features

*   **Register Classes:** Add new disciplines with a unique ID, name, and optional semester.
    *   `/register_class <id> <name> [semester]`
*   **Add Absences:** Increment absence count for a specific class.
    *   `/add_absence <class_id>`
*   **View Class Absences:** Check the number of absences for a particular discipline.
    *   `/my_absences <class_id>`
*   **View Total Absences:** Get a sum of all absences across all registered disciplines.
    *   `/total_absences`
*   **List Registered Classes:** See all disciplines you have registered.
    *   `/list_classes`
*   **Help:** Get a list of all available commands.
    *   `/help`

## Technologies Used

*   **Python 3.12**: The core programming language.
*   **Telebot**: Python framework for Telegram Bot API.
*   **Pipenv**: For managing project dependencies and virtual environments.
*   **PostgreSQL**: The relational database for storing data.
*   **Alembic**: Database migration tool for managing schema changes.
*   **Docker & Docker Compose**: For containerizing the application and its services, ensuring easy setup and deployment.

## Setup

Follow these steps to get the bot up and running on your local machine.

### Prerequisites

Make sure you have the following installed:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/telegram-absence-counter.git # Replace with your actual repo URL
cd telegram-absence-counter
```

### 2. Environment Variables

Create a `.env` file in the root directory of the project and populate it with your Telegram Bot Token and PostgreSQL database credentials. You can use `.env.example` as a template.

```
# .env example
BOT_TOKEN=

PG_HOST=
PG_DATABASE=
PG_USER=
PG_PASSWORD=
PG_PORT=
LOG_LEVEL=
```

*   `BOT_TOKEN`: Obtain this from BotFather on Telegram.
*   `PG_HOST`: Set to `postgres` as it's the service name in `docker-compose.yml`.
*   `PG_DATABASE`: The name of the database your bot will use.
*   `PG_USER`, `PG_PASSWORD`: Credentials for your PostgreSQL user.
*   `PG_PORT`: The port PostgreSQL is running on (default is 5432).
*   `PG_BASE_DATABASE`: The default database used for initial connection before connecting to `PG_DATABASE`.
*   `LOG_LEVEL`: Set to `INFO` or `DEBUG` for logging verbosity.

### 3. Running the Bot

Build the Docker images and start all services:

```bash
docker-compose build
docker-compose up
```

The bot should now be running and accessible via Telegram.

## Usage

Start a chat with your bot on Telegram and use the commands listed in the [Features](#features) section.

## Project Structure

```
telegram-absence-counter/
├── app/
│   ├── main.py                 # Main bot entry point
│   ├── src/
│   │   └── bot_handler.py      # Handles bot commands and logic
│   └── database/
│       ├── base.py             # Low-level PostgreSQL connection and query execution
│       ├── bot_db.py           # High-level database operations for bot features
│       └── migrations/         # Alembic database migration scripts
├── docker-compose.yml          # Defines Docker services (bot, postgres)
├── Dockerfile                  # Instructions to build the bot's Docker image
├── Pipfile                     # Project dependencies managed by Pipenv
├── Pipfile.lock                # Locked dependencies for reproducible builds
├── alembic.ini                 # Alembic configuration file
├── .env.example                # Example environment variables file
├── .dockerignore               # Files/folders to ignore when building Docker images
├── .gitignore                  # Files/folders to ignore in Git
└── README.md                   # Project documentation (this file)
```
