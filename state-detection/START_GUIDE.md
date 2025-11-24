# Qontinui Mac - Quick Start Guide

## ✅ Setup Complete!

Your qontinui development environment is ready to use on Mac!

## 🐳 Docker Services (Already Running)

```bash
# Check status
docker ps

# Stop services
cd ~/Documents/qontinui/qontinui-web
docker compose down

# Start services
cd ~/Documents/qontinui/qontinui-web
docker compose up -d
```

**Running Services:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO: `localhost:9000` (API), `localhost:9001` (Console)

## 🚀 Starting Services

### Method 1: Using Helper Scripts (Easiest)

Open separate terminal windows for each service:

**Terminal 1 - Web Backend:**
```bash
cd ~/Documents/qontinui/qontinui-web/backend
./start-backend.sh
```

**Terminal 2 - Web Frontend:**
```bash
cd ~/Documents/qontinui/qontinui-web/frontend
./start-frontend.sh
```

**Terminal 3 - API Service (Optional):**
```bash
cd ~/Documents/qontinui/qontinui-api
./start-api.sh
```

**Terminal 4 - Runner (Optional):**
```bash
cd ~/Documents/qontinui/qontinui-runner
npm run tauri dev
```

### Method 2: Manual Commands

**Web Backend:**
```bash
cd ~/Documents/qontinui/qontinui-web/backend
source venv/bin/activate
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Web Frontend:**
```bash
cd ~/Documents/qontinui/qontinui-web/frontend
npm run dev
```

## 🌐 Access URLs

Once all services are running:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Service:** http://localhost:8001
- **MinIO Console:** http://localhost:9001

## 📋 Service Status

| Service | Port | Status | Command to Start |
|---------|------|--------|------------------|
| PostgreSQL | 5432 | ✅ Running (Docker) | `docker compose up -d` |
| Redis | 6379 | ✅ Running (Docker) | `docker compose up -d` |
| MinIO | 9000-9001 | ✅ Running (Docker) | `docker compose up -d` |
| Backend | 8000 | ⏳ Ready to start | `./start-backend.sh` |
| Frontend | 3000 | ⏳ Ready to start | `./start-frontend.sh` |
| API | 8001 | ⏳ Ready to start | `./start-api.sh` |

## 🔧 First Time Setup Complete!

The following have been configured:

✅ Python 3.12.12 installed
✅ Docker containers running (PostgreSQL, Redis, MinIO)
✅ Backend virtual environment created with Poetry
✅ Environment files created (.env)
✅ Startup scripts created

## 📝 Next Steps

1. **Start the Web Backend** (Terminal 1):
   ```bash
   cd ~/Documents/qontinui/qontinui-web/backend
   ./start-backend.sh
   ```

2. **Install and Start Frontend** (Terminal 2):
   ```bash
   cd ~/Documents/qontinui/qontinui-web/frontend
   npm install  # First time only
   ./start-frontend.sh
   ```

3. **Open your browser** to http://localhost:3000

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using a port (e.g., 8000)
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart Docker containers
cd ~/Documents/qontinui/qontinui-web
docker compose restart
```

### Backend Won't Start
```bash
cd ~/Documents/qontinui/qontinui-web/backend
source venv/bin/activate

# Check if alembic is installed
which alembic

# Reinstall if needed
poetry install
```

### Frontend Build Errors
```bash
cd ~/Documents/qontinui/qontinui-web/frontend

# Clean install
rm -rf node_modules package-lock.json
npm install
```

## 💡 Useful Commands

**Check what's running:**
```bash
# Docker containers
docker ps

# All Python processes
ps aux | grep python

# All Node processes
ps aux | grep node
```

**View logs:**
```bash
# Docker logs
docker compose logs -f

# Backend logs (if using the script)
cd ~/Documents/qontinui/qontinui-web/backend
tail -f logs/*.log  # If logs are configured
```

**Database migrations:**
```bash
cd ~/Documents/qontinui/qontinui-web/backend
source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## 🔄 Daily Workflow

**Start Everything:**
```bash
# 1. Start Docker (if not running)
cd ~/Documents/qontinui/qontinui-web && docker compose up -d

# 2. Open 2 terminals and run:
cd ~/Documents/qontinui/qontinui-web/backend && ./start-backend.sh
cd ~/Documents/qontinui/qontinui-web/frontend && ./start-frontend.sh
```

**Stop Everything:**
```bash
# Stop web services (Ctrl+C in each terminal)
# Stop Docker
cd ~/Documents/qontinui/qontinui-web && docker compose down
```

## 📚 Documentation

- Backend API Docs: http://localhost:8000/docs (when running)
- Frontend: Check `qontinui-web/frontend/README.md`
- Runner: Check `qontinui-runner/README.md`
- API: Check `qontinui-api/README.md`

## 🎯 Quick Reference

**Python Version:**
- Web Backend: Python 3.12.12 (`/usr/local/bin/python3.12`)
- API Service: Python 3.11+ (uses system python3)
- Runner: Python 3.10+ (uses Poetry environments)

**Environment Files:**
- Backend: `qontinui-web/backend/.env`
- Frontend: `qontinui-web/frontend/.env.local`
- API: `qontinui-api/.env`

**Database:**
- Host: `localhost`
- Port: `5432`
- Database: `qontinui_db`
- User: `qontinui_user`
- Password: `qontinui_dev_password` (dev only)

---

**Need Help?** Check the `SETUP_STATUS.md` file for more detailed information.
