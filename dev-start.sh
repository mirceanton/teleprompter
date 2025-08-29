#!/bin/bash

echo "🚀 Starting Remote Teleprompter Microservices Development Environment"

# Kill any existing processes
pkill -f "python3.*main.py"
pkill -f "npm.*dev"

# Start backend API
echo "📡 Starting Backend API on port 8001..."
cd backend && python3 main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start landing page
echo "🏠 Starting Landing Page on port 3000..."
cd ../landing && npm run dev &
LANDING_PID=$!

# Start controller
echo "💻 Starting Controller App on port 3001..."
cd ../controller && npm run dev &
CONTROLLER_PID=$!

# Start teleprompter
echo "📱 Starting Teleprompter App on port 3002..."
cd ../teleprompter && npm run dev &
TELEPROMPTER_PID=$!

# Wait for services to start
sleep 5

echo ""
echo "✅ All services started!"
echo "📡 Backend API:      http://localhost:8001/api/health"
echo "🏠 Landing Page:     http://localhost:3000"
echo "💻 Controller:       http://localhost:3001"
echo "📱 Teleprompter:     http://localhost:3002"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $LANDING_PID $CONTROLLER_PID $TELEPROMPTER_PID 2>/dev/null
    pkill -f "python3.*main.py"
    pkill -f "npm.*dev"
    echo "✅ All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM

# Wait for user input
while true; do
    sleep 1
done