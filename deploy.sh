#!/bin/bash
# AI Attendance System - Deployment Script

set -e

echo "🚀 AI Attendance System Deployment"
echo "==================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

echo "✅ Docker and docker-compose are available"

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/face_encodings data/attendance data/faces logs config

# Build and start the system
echo "🏗️ Building Docker image..."
docker-compose build

echo "🚀 Starting the system..."
docker-compose up -d

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📊 Services:"
echo "  • Streamlit UI: http://localhost:8501"
echo ""
echo "📋 Management commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop system: docker-compose down"
echo "  • Restart: docker-compose restart"
echo ""
echo "📂 Data persistence:"
echo "  • Student data: ./data/"
echo "  • Logs: ./logs/"
echo "  • Configuration: ./config/"
echo ""
echo "⚠️  Make sure your camera is accessible to Docker"
echo "   You may need to adjust device permissions or camera source"