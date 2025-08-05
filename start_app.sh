#!/bin/bash

# Start the HR Assistant application with both backend and frontend

echo "🚀 Starting HR Assistant Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📋 Installing Python dependencies..."
pip install -r requirements.txt

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start the FastAPI backend in the background
echo "🐍 Starting FastAPI backend server..."
python api_server.py &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 3

# Start the React frontend
echo "⚛️  Starting React frontend..."
npm run dev &
FRONTEND_PID=$!

echo "✅ Application started successfully!"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script termination
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
