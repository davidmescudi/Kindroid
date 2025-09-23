#!/bin/bash

# Stop on any error
set -e

# --- Configuration ---
SERVICE_NAME="kindroid.service"
SERVICE_FILE_PATH="/etc/systemd/system/$SERVICE_NAME"
PYTHON_EXEC="[REPLACE_WITH_ACTUAL_PATH]/kindroid/bin/python"
SCRIPT_PATH="[REPLACE_WITH_ACTUAL_PATH]/kindroid/main_gpio.py"
WORKING_DIR="[REPLACE_WITH_ACTUAL_PATH]/kindroid/"
USER_NAME="[REPLACE_WITH_ACTUAL_USERNAME]"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root. Please use 'sudo ./setup_service.sh'" >&2
  exit 1
fi

echo "--- Creating systemd service file at $SERVICE_FILE_PATH ---"

# Use a 'here document' to write the service file configuration
cat > "$SERVICE_FILE_PATH" << EOF
[Unit]
Description=My PipeCat Project
After=network.target

[Service]
ExecStart=$PYTHON_EXEC $SCRIPT_PATH
WorkingDirectory=$WORKING_DIR
StandardOutput=inherit
StandardError=inherit
Restart=always
User=$USER_NAME

[Install]
WantedBy=multi-user.target
EOF

# Set the correct permissions for the service file
chmod 644 "$SERVICE_FILE_PATH"

echo "--- Reloading systemd daemon ---"
systemctl daemon-reload

echo "--- Enabling service to start on boot ---"
systemctl enable "$SERVICE_NAME"

echo "--- Starting service now ---"
systemctl start "$SERVICE_NAME"

echo ""
echo "✅ Setup complete!"
echo "Your service '$SERVICE_NAME' is now enabled and running."
echo ""
echo "To check the status, run:"
echo "sudo systemctl status $SERVICE_NAME"
echo ""
echo "To see the live logs, run:"
echo "journalctl -u $SERVICE_NAME -f"
