#!/bin/bash

echo "🚀 Starting Unity Docs MCP Inspector"
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Kill any existing processes
pkill -f mcp-inspector 2>/dev/null || echo "No existing inspector processes"
lsof -ti :6274 | head -1 | xargs kill -9 2>/dev/null || true
lsof -ti :6277 | head -1 | xargs kill -9 2>/dev/null || true
sleep 3

# Start MCP Inspector with direct command
echo "📡 Starting MCP Inspector..."
export DANGEROUSLY_OMIT_AUTH=true
export PYTHONPATH=/Users/hiko/Desktop/unity-docs-mcp/src
cd /Users/hiko/Desktop/unity-docs-mcp
/Users/hiko/.asdf/installs/nodejs/lts/bin/mcp-inspector /Users/hiko/Desktop/unity-docs-mcp/venv/bin/python -m unity_docs_mcp.server > inspector.log 2>&1 &
INSPECTOR_PID=$!

# Wait for startup
sleep 5

echo ""
echo "✅ MCP Inspector started successfully!"
echo "🆔 Process ID: $INSPECTOR_PID"
echo ""
echo "🌐 Open in browser:"
echo "   http://localhost:6274"
echo ""
echo "🧪 Test Tools Available:"
echo "   1. list_unity_versions"
echo "   2. suggest_unity_classes" 
echo "   3. get_unity_api_doc"
echo "   4. search_unity_docs"
echo ""
echo "📝 Example test inputs:"
echo "   Tool 1: {}"
echo "   Tool 2: {\"partial_name\": \"game\"}"
echo "   Tool 3: {\"class_name\": \"GameObject\", \"version\": \"6000.0\"}"
echo "   Tool 4: {\"query\": \"transform\", \"version\": \"6000.0\"}"
echo ""
echo "🔴 To stop: run 'pkill -f mcp-inspector'"
echo ""

# Check if process is running and extract token
sleep 3
if ps -p $INSPECTOR_PID > /dev/null; then
    echo "✅ Inspector process is running (PID: $INSPECTOR_PID)"
    
    # Wait for log file and check status
    sleep 2
    if [ -f inspector.log ]; then
        echo ""
        echo "📋 Inspector Log:"
        tail -5 inspector.log
        
        # Check if authentication is disabled
        if grep -q "Authentication is disabled" inspector.log; then
            echo ""
            echo "✅ Authentication is DISABLED - you can connect directly!"
            echo "🌐 Go to: http://localhost:6274"
        else
            echo ""
            echo "🔑 Looking for authentication token..."
            if grep -q "MCP_PROXY_AUTH_TOKEN" inspector.log; then
                echo "Token found in log"
                grep "MCP_PROXY_AUTH_TOKEN" inspector.log | tail -1
            fi
        fi
    fi
    
    echo ""
    echo "🎯 Ready for testing!"
else
    echo "❌ Inspector process failed to start"
    echo "Check inspector.log for details:"
    cat inspector.log 2>/dev/null || echo "No log file found"
fi