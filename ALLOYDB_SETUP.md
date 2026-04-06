# AlloyDB Setup Guide

This guide walks you through setting up Google Cloud AlloyDB for the Multi-Agent Productivity Tracker. The `Reflection Agent` uses this database to store daily productivity summaries.

## 1. Create an AlloyDB Cluster and Instance

Refer to below document to create a alloydb database cluster
https://codelabs.developers.google.com/quick-alloydb-setup?hl=en#0

## 2. Connect to the Database

If you are running the application locally, the easiest way to connect securely is using the **AlloyDB Auth Proxy**.

1. Download and install the AlloyDB Auth Proxy.
2. Start the proxy to listen on a local port (e.g., 5432):
   ```bash
   ./alloydb-auth-proxy "projects/YOUR_PROJECT/locations/YOUR_REGION/clusters/YOUR_CLUSTER/instances/YOUR_INSTANCE"
   ```


## 3. Create the Database and Table

Go to Gcp console sarech for alloydb and navigate to alloydb studio, run the following commands to create the target database and the specific table schema required by `agent.py`:

```sql
-- Create the database
CREATE DATABASE productivity_db;

-- Connect to the newly created database
\c productivity_db;

-- Create the table for the Reflection Agent
CREATE TABLE productivity_history (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(255),
    summary TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create the table for User Profiles & History
CREATE TABLE user_profiles (
    name VARCHAR(255) PRIMARY KEY,
    role VARCHAR(255),
    preferred_work_start INT DEFAULT 9,
    preferred_work_end INT DEFAULT 17,
    work_style VARCHAR(50),
    goals JSONB,
    total_sessions INT DEFAULT 0,
    avg_completion_rate FLOAT DEFAULT 0.0,
    total_deep_work_hours INT DEFAULT 0,
    last_active DATE,
    history JSONB
);
```

## 4. Configure Environment Variables

Update your project's `.env` file to match the database configuration. The `save_day` tool in `agent.py` expects the following environment variables:

```env
# .env

# The Gemini API key (already required for the agents)
GEMINI_API_KEY=your_gemini_api_key

# AlloyDB Configuration
# Use 127.0.0.1 if using the AlloyDB Auth Proxy locally, 
# otherwise use the private IP of your AlloyDB instance.
ALLOYDB_HOST=127.0.0.1
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your_secure_password
ALLOYDB_DB_NAME=productivity_db
```

## 5. Install Python Database Dependencies

Ensure that you have installed the PostgreSQL adapter for Python. If it's not already in your `requirements.txt`, you will need to install it:

```bash
# For standard local development (uses pre-compiled binaries)
pip install psycopg2-binary

# OR if you have pg_config and C compilers installed
pip install psycopg2
```
