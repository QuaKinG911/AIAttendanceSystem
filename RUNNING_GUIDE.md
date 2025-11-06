# 🚀 Step-by-Step Guide to Run the Enhanced AI Attendance System

## Prerequisites

Before running the system, ensure you have:
- Linux/macOS/Windows with Docker support
- At least 4GB RAM
- 2GB free disk space
- Webcam (for live attendance)

---

## Method 1: Docker Deployment (Recommended)

### Step 1: Install Docker and Docker Compose
```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# On CentOS/RHEL/Fedora
sudo dnf install docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

### Step 2: Clone and Navigate to Project
```bash
cd /home/quaking911/github/ai-attendance-system
```

### Step 3: Start All Services
```bash
# Build and start all containers (PostgreSQL, Redis, Flask app)
docker-compose up --build
```

### Step 4: Wait for Services to Start
Wait for the following messages:
- "PostgreSQL database server" - Database ready
- "valkey" - Redis ready
- "AI Attendance System Web Application" - Flask app ready

### Step 5: Access the Application
Open your browser and go to: **http://localhost:5000**

---

## Method 2: Manual Installation

### Step 1: Install System Dependencies
```bash
# PostgreSQL and Redis
sudo dnf install postgresql-server postgresql-contrib redis

# Initialize and start PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Start Redis
sudo systemctl start valkey
sudo systemctl enable valkey
```

### Step 2: Set Up Python Environment
```bash
cd /home/quaking911/github/ai-attendance-system

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Database
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE ai_attendance;"
sudo -u postgres psql -c "CREATE USER attendance_user WITH PASSWORD 'attendance_pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_attendance TO attendance_user;"

# Run database migrations
alembic upgrade head

# Populate with test data
python migrate_data.py
```

### Step 4: Start the Web Application
```bash
# Start the Flask web application
python run_web.py
```

### Step 5: Access the Application
Open your browser and go to: **http://localhost:5000**

---

## 🔐 Login Credentials

| Role    | Username  | Password   | Access Level |
|---------|-----------|------------|--------------|
| Admin   | admin     | admin123   | Full system control |
| Teacher | teacher1  | teacher123 | Class management |
| Student | student1  | student123 | Personal attendance |

---

## 🎯 Using the System

### For Students
1. **Login** with student credentials
2. **View Dashboard**: See today's classes and attendance summary
3. **Check Attendance**: View personal attendance records by class
4. **Download Reports**: Export attendance history

### For Teachers
1. **Login** with teacher credentials
2. **Start Sessions**: Begin attendance for your classes
3. **Monitor Live Feed**: Watch real-time attendance as students arrive
4. **Edit Records**: Manually adjust attendance if needed
5. **Export Data**: Download Excel/CSV reports

### For Admins
1. **Login** with admin credentials
2. **Manage Users**: Add/edit/delete students and teachers
3. **Create Classes**: Set up class schedules and assign teachers
4. **View Analytics**: Monitor system-wide attendance statistics
5. **System Settings**: Configure attendance windows and policies

---

## 🧪 Testing the System

### Test API Endpoints
```bash
# Test health check
curl http://localhost:5000/api/health

# Test login (replace with actual credentials)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Test AI Attendance
```bash
# Run the original AI attendance system
python main.py
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://attendance_user:attendance_pass@127.0.0.1/ai_attendance

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here

# Redis Configuration
REDIS_URL=redis://127.0.0.1:6379/0

# Attendance Configuration
ATTENDANCE_PRESENT_WINDOW_MINUTES=5
ATTENDANCE_LATE_WINDOW_MINUTES=15
ATTENDANCE_CONFIDENCE_THRESHOLD=0.7
ATTENDANCE_LIVENESS_THRESHOLD=0.6
```

### Attendance Settings
- **Present Window**: 5 minutes (students detected within this time = Present)
- **Late Window**: 15 minutes (students detected after present but within late = Late)
- **Absent**: After late window expires

---

## 🐳 Docker Commands

```bash
# View running containers
docker ps

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up --build --force-recreate

# Clean up
docker system prune -a
```

---

## 🔍 Troubleshooting

### Common Issues

**1. Database Connection Failed**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database
sudo -u postgres dropdb ai_attendance
sudo -u postgres createdb ai_attendance
alembic upgrade head
python migrate_data.py
```

**2. Port 5000 Already in Use**
```bash
# Kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9

# Or use different port
FLASK_RUN_PORT=5001 python run_web.py
```

**3. Camera Not Detected**
```bash
# List available cameras
python -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).read()[0]])"

# Run with specific camera
python main.py --camera 1
```

**4. Permission Errors**
```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
# Logout and login again
```

**5. Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 System Monitoring

### Health Checks
- **API Health**: http://localhost:5000/api/health
- **Database**: Check PostgreSQL logs
- **Redis**: Check Valkey service status

### Performance Monitoring
- **CPU/Memory**: Use `htop` or `top`
- **Database**: `sudo -u postgres psql -d ai_attendance -c "SELECT * FROM pg_stat_activity;"`
- **Logs**: Check `attendance_system.log`

---

## 🎓 Next Steps

1. **Add Student Photos**: Use the dataset creation tools
2. **Configure Classes**: Set up your actual class schedules
3. **Test AI Recognition**: Run attendance sessions with real students
4. **Customize Settings**: Adjust attendance windows and thresholds
5. **Set Up Notifications**: Configure email/SMS alerts

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs in `attendance_system.log`
3. Test individual components
4. Check system requirements

**The system is now ready for production use!** 🎓✨