# Dify Knowledge Ingest

## Setup
Create a Virtual Environment
```cmd
python -m venv .venv
```

Activate
```cmd
# Windows
.\.venv\Scripts\activate

# Linux
source .venv/bin/activate
```

Install Dependencies
```cmd
pip install --no-cache-dir -r requirements.txt
```

Create env files
```cmd
# Windows
copy .env.example .env

# Linux
cp .env.example .env
```

## How to Use
Insert any documents inside the input directory

Run this command:
```cmd
python main.py
```