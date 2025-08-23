# PostgreSQL Setup Guide for Stock Scanner

## Quick Setup Steps

### Option 1: Using pgAdmin (Recommended)

1. **Open pgAdmin** (should be installed with PostgreSQL)
   - Look for pgAdmin in your Start menu
   - Default URL: http://localhost/pgadmin4

2. **Connect to PostgreSQL Server**
   - Right-click "Servers" → "Register" → "Server"
   - Name: `Local PostgreSQL`
   - Host: `localhost`
   - Port: `5432`
   - Username: `postgres`
   - Password: (set during PostgreSQL installation)

3. **Create Database**
   - Right-click "Databases" → "Create" → "Database"
   - Database name: `stock_scanner`
   - Owner: `postgres`
   - Click "Save"

4. **Create User**
   - Right-click "Login/Group Roles" → "Create" → "Login/Group Role"
   - General tab: Name: `stock_scanner`
   - Definition tab: Password: `password123`
   - Privileges tab: Check "Can login?" and "Superuser?"
   - Click "Save"

5. **Grant Permissions**
   - Right-click the `stock_scanner` database → "Properties"
   - Security tab → Add the `stock_scanner` user with all privileges

### Option 2: Command Line Setup

If you know the postgres password, run these commands:

```bash
# Connect to PostgreSQL as postgres user
psql -U postgres

# Then run these SQL commands:
CREATE DATABASE stock_scanner;
CREATE USER stock_scanner WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE stock_scanner TO stock_scanner;
\q
```

### Option 3: Reset PostgreSQL Password

If you don't remember the postgres password:

1. **Stop PostgreSQL Service**
   ```powershell
   Stop-Service postgresql-x64-17
   ```

2. **Edit pg_hba.conf** (as Administrator)
   - File location: `C:\Program Files\PostgreSQL\17\data\pg_hba.conf`
   - Change the line:
     ```
     host    all             all             127.0.0.1/32            scram-sha-256
     ```
     to:
     ```
     host    all             all             127.0.0.1/32            trust
     ```

3. **Start PostgreSQL Service**
   ```powershell
   Start-Service postgresql-x64-17
   ```

4. **Connect and Set Password**
   ```bash
   psql -U postgres
   ALTER USER postgres PASSWORD 'admin123';
   \q
   ```

5. **Restore pg_hba.conf** (change `trust` back to `scram-sha-256`)

6. **Restart PostgreSQL Service**
   ```powershell
   Restart-Service postgresql-x64-17
   ```

## Verification

After setup, test the connection:

```bash
psql -U stock_scanner -d stock_scanner -h localhost
```

You should see:
```
Password for user stock_scanner: [enter: password123]
stock_scanner=#
```

## Environment Configuration

Update your `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://stock_scanner:password123@localhost:5432/stock_scanner
POSTGRES_USER=stock_scanner
POSTGRES_PASSWORD=password123
POSTGRES_DB=stock_scanner
```

## Troubleshooting

### Connection Refused
- Check if PostgreSQL service is running: `Get-Service postgresql-x64-17`
- Start if needed: `Start-Service postgresql-x64-17`

### Authentication Failed
- Verify username and password
- Check pg_hba.conf configuration
- Try connecting with different authentication methods

### Permission Denied
- Ensure the user has proper privileges on the database
- Grant additional permissions if needed

## Next Steps

Once PostgreSQL is set up:

1. Initialize the database schema:
   ```bash
   cd backend
   python app/init_db.py
   ```

2. Start the backend server:
   ```bash
   python run_server.py
   ```

3. Set up and start the frontend (in a new terminal):
   ```bash
   cd frontend
   npm install
   npm start
   ```

The application will be available at http://localhost:3000