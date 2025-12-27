# Database Configuration Files

This directory contains JSON configuration files for each database. Each file stores both metadata (for UI display) and connection credentials.

## Structure

```json
{
  "metadata": {
    "db_key": "your_db_key",
    "name": "Your Database Name",
    "description": "Brief description",
    "tables": {
      "table1": "Description of table1",
      "table2": "Description of table2"
    }
  },
  "config": {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "your_database_name",
    "user": "your_username",
    "password": "your_password",
    "ssl": false
  }
}
```

## Adding a New Database

1. Create a new JSON file: `databases/your_db_key.json`
2. Fill in the `metadata` section (for UI display)
3. Fill in the `config` section with your database credentials
4. The application will automatically detect and load it

## Removing a Database

Simply delete the corresponding JSON file from this directory.

## Security Note

⚠️ **Important**: These JSON files contain sensitive credentials. Make sure to:
- Add `databases/*.json` to `.gitignore` if storing passwords
- Use environment variables for passwords in production (see below)
- Never commit credentials to version control

## Using Environment Variables for Passwords

You can use environment variables in the password field:

```json
{
  "config": {
    "password": "${ECOM_DB_PASSWORD}"
  }
}
```

The tool will automatically resolve environment variables.

## Supported Database Types

Currently supported:
- `postgresql` - PostgreSQL databases

Future support planned:
- `mysql` - MySQL/MariaDB
- `mongodb` - MongoDB (NoSQL)
- `sqlite` - SQLite

## File Naming Convention

- Use lowercase with underscores: `your_db_name.json`
- The `db_key` in metadata should match the filename (without .json extension)
