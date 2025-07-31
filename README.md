# Avatar HR Assistant

This project aims at reimagining user experience with HR processes.

## Prerequisites

- Docker and Docker Compose
- Python

## Getting Started

### Using Docker Compose

Use Docker Compose to run the database and Adminer (alternative to phpMyAdmin):

1. **Start the services**:
   ```bash
   docker compose up -d
   ```
   This will start:
   - MySQL database on port 3307
   - Adminer (database management) on port 8080

2. **Stop the services**:
   ```bash
   docker compose down
   ```

3. **View logs**:
   ```bash
   docker compose logs -f
   ```

### Accessing Adminer

Adminer provides a web interface to manage the MySQL database:

1. Open your browser and go to: `http://localhost:8080`
2. Login with the following credentials:
   - System: MySQL / MariaDB
   - Server: `mysql_eis`
   - Username: `eis_user`
   - Password: `eis_pass`
   - Database: `eis`

### Database Initialization

The database is automatically initialized with the schema and data from `eis.sql` on first run.

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```

4. Start the MCP server:
   ```bash
   python mcp_server.py
   ```

## Project Structure

- `agent.py` - Main agent implementation
- `mcp_server.py` - FastMCP server exposing Kimble operations
- `clients/` - API clients (Kimble, etc.)
- `config.py` - Configuration management
- `exceptions.py` - Custom exceptions
