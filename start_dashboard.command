#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "============================================="
echo "   Starting Horse Racing Edge Dashboard...   "
echo "============================================="
echo "Working Directory: $DIR"

# Launch Frontend in a new Terminal window/tab
osascript <<EOF
tell application "Terminal"
    do script "cd '$DIR/frontend' && npm run dev || read -p 'Press Enter to close'"
end tell
EOF

# Launch Backend in a new Terminal window/tab
osascript <<EOF
tell application "Terminal"
    do script "cd '$DIR/backend' && source venv/bin/activate && uvicorn main:app --reload --port 8000 || read -p 'Press Enter to close'"
end tell
EOF

# Give servers time to bind ports
echo "Waiting for servers to start..."
sleep 5

# Open browser to dashboard
open "http://localhost:3000"

echo "============================================="
echo "   Dashboard Launched!                       "
echo "============================================="
echo "Two new Terminal windows have opened running the backend and frontend."
echo "You can minimize them, but do not close them while using the dashboard."
echo "Press any key to close this launcher..."
read -n 1
