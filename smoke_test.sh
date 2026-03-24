#!/bin/bash

# Kartavya-3.0 Smoke Test Script
# This script verify that the local Docker deployment is running correctly.

echo "🚀 Starting Kartavya-3.0 Smoke Test..."

# 1. Check Backend Health
echo -n "Checking Backend Health (localhost:8000)... "
HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ HEALTHY"
else
    echo "❌ FAILED (Response: $HEALTH_RESPONSE)"
fi

# 2. Check Frontend Accessibility
echo -n "Checking Frontend (localhost:3000)... "
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:3000)
if [ "$HTTP_STATUS" == "200" ]; then
    echo "✅ ONLINE"
else
    echo "❌ OFFLINE (Status Code: $HTTP_STATUS)"
fi

# 3. Check for API Key in logs
echo -n "Checking Backend Logs for Errors... "
INVALID_KEY_ERR=$(docker logs kartavya-backend 2>&1 | grep "API key not valid" | tail -n 1)
if [ -n "$INVALID_KEY_ERR" ]; then
    echo "⚠️ WARNING: API key invalid or missing in logs. Please update .env"
else
    echo "✅ No API key errors found in recent logs."
fi

echo "🏁 Smoke Test Complete."
