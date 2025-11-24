# Fixes Applied - Backend Setup

## Issues Fixed

### 1. ✅ Database Connection Issue
**Problem**: Local PostgreSQL@15 was running and conflicting with Docker PostgreSQL
**Fix**: Stopped local PostgreSQL service
```bash
brew services stop postgresql@15
```

**To restart local PostgreSQL later** (if needed for other projects):
```bash
brew services start postgresql@15
```

### 2. ✅ IPv4/IPv6 Connection Issue
**Problem**: Connection trying IPv6 (::1) instead of IPv4
**Fix**: Changed DATABASE_URL in `.env` from `localhost` to `127.0.0.1`

### 3. ✅ Wrong Main Module
**Problem**: Script was calling `uvicorn main:app` but file is `run.py`
**Fix**: Updated `start-backend.sh` to use `python run.py`

### 4. ✅ Database Migration Error
**Problem**: Foreign key type mismatch - `project_id` was UUID but should be Integer
**Fix**: Fixed migration file `e45f9b2c3d1a_add_snapshot_tables_for_integration_testing.py`
Changed: `sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True)`
To: `sa.Column("project_id", sa.Integer(), nullable=True)`

### 5. ✅ Database Schema Reset
**Problem**: Partial migration left database in bad state
**Fix**: Dropped and recreated schema
```bash
docker exec qontinui-postgres psql -U qontinui_user -d qontinui_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

### 6. ⏳ Missing OpenCV (In Progress)
**Problem**: `ModuleNotFoundError: No module named 'cv2'`
**Status**: Installing OpenCV (opencv-python) - this takes 5-10 minutes to build
**Command Running**:
```bash
pip install opencv-python
```

## Next Steps

Once OpenCV finishes installing (you'll see "Successfully installed opencv-python" in your terminal):

1. **Run migrations again**:
   ```bash
   cd ~/Documents/qontinui/qontinui-web/backend
   source venv/bin/activate
   alembic upgrade head
   ```

2. **Start the backend**:
   ```bash
   ./start-backend.sh
   ```

3. **Verify it's working**:
   - Backend should start without errors
   - Visit http://localhost:8000/docs to see API documentation
   - You should see the Swagger UI

4. **Start the frontend** (in a new terminal):
   ```bash
   cd ~/Documents/qontinui/qontinui-web/frontend
   npm install  # First time only
   npm run dev
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## Summary of Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Docker (PostgreSQL, Redis, MinIO) | ✅ Running | Port 5432, 6379, 9000-9001 |
| Python 3.12 | ✅ Installed | /usr/local/bin/python3.12 |
| Backend Dependencies | ⏳ Installing | OpenCV building (5-10 min) |
| Database Schema | ✅ Reset | Ready for clean migration |
| Migration Files | ✅ Fixed | Type mismatch corrected |
| Environment Config | ✅ Fixed | DATABASE_URL uses 127.0.0.1 |
| Startup Scripts | ✅ Fixed | Uses correct entry point |

## Configuration Changes Made

### `.env` file:
- Changed: `DATABASE_URL=postgresql://qontinui_user:qontinui_dev_password@localhost:5432/qontinui_db`
- To: `DATABASE_URL=postgresql://qontinui_user:qontinui_dev_password@127.0.0.1:5432/qontinui_db`

### `start-backend.sh`:
- Changed: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- To: `python run.py`

### Migration file `e45f9b2c3d1a_add_snapshot_tables_for_integration_testing.py`:
- Changed `project_id` type from UUID to Integer

## Monitoring OpenCV Installation

To check if OpenCV is still installing:
```bash
ps aux | grep -i "pip install opencv"
```

When it finishes, you'll see in your terminal:
```
Successfully installed numpy-2.x.x opencv-python-4.x.x
```

## Troubleshooting

**If backend still won't start after OpenCV installs:**
```bash
cd ~/Documents/qontinui/qontinui-web/backend
source venv/bin/activate

# Check if cv2 is available
python -c "import cv2; print('OpenCV version:', cv2.__version__)"

# If not, reinstall
pip install --force-reinstall opencv-python
```

**If you need to use local PostgreSQL again:**
```bash
# Change Docker port to 5433
cd ~/Documents/qontinui/qontinui-web
# Edit docker-compose.yml and change "5432:5432" to "5433:5432"
# Then update .env DATABASE_URL to use port 5433

# Start local PostgreSQL
brew services start postgresql@15
```

## Files Modified

1. `/Users/jspinak/Documents/qontinui/qontinui-web/backend/.env`
2. `/Users/jspinak/Documents/qontinui/qontinui-web/backend/start-backend.sh`
3. `/Users/jspinak/Documents/qontinui/qontinui-web/backend/alembic/versions/e45f9b2c3d1a_add_snapshot_tables_for_integration_testing.py`

## Documentation Created

1. `START_GUIDE.md` - Daily workflow and commands
2. `SETUP_STATUS.md` - Detailed setup information
3. `FIXES_APPLIED.md` - This file - all fixes and changes made
