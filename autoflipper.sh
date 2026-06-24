#!/bin/bash
APP_DIR="USP_MiniProject"

echo "Starting Auto-Flipper Bot... (Press Ctrl+C to stop)"

#loop
while true; do
    echo "--------------------------------"
    echo "Running new cycle at $(date)"
    
    echo "Pulling latest changes..."
    git pull

    LIVE_CONFIG="$APP_DIR/config.json"
    
    # Check if the live config contains Standby
    if grep -q '"theme_name": "Standby"' $LIVE_CONFIG; then
        echo "Current state is STANDBY. Toggling to ACTIVE..."
        cp "$APP_DIR/config.active.json" $LIVE_CONFIG
        COMMIT_MSG="BOT: Activating AI Core"

    else
        echo "Current state is ACTIVE. Toggling back to STANDBY..."
        cp "$APP_DIR/config.standby.json" $LIVE_CONFIG
        COMMIT_MSG="BOT: Resetting to Standby"
    fi
    
    #push changes
    echo "Committing and pushing change..."
    git add $LIVE_CONFIG
    git commit -m "$COMMIT_MSG"
    git push origin main
    
    echo "Push successful. GitOps pipeline triggered."
    echo "Waiting 30 seconds before next cycle..."
    sleep 30

done