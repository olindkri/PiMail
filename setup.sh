#!/bin/bash
# PiMail Setup Script for Raspberry Pi
# Run this on the Pi after copying the project to /home/olindkri/PiMail

set -e

PIMAIL_DIR="/home/olindkri/PiMail"
USER="olindkri"

echo "=== PiMail Setup ==="

# Install system dependencies
echo "[1/6] Installing system packages..."
sudo apt update
sudo apt install -y chromium unclutter python3-pip python3-venv

# Create Python virtual environment
echo "[2/6] Setting up Python environment..."
cd "$PIMAIL_DIR"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Create .env from example if it doesn't exist
if [ ! -f "$PIMAIL_DIR/.env" ]; then
    echo "[3/6] Creating .env from template..."
    cp .env.example .env
    echo ""
    echo ">>> IMPORTANT: Edit $PIMAIL_DIR/.env with your IMAP credentials <<<"
    echo ">>> Run: nano $PIMAIL_DIR/.env <<<"
    echo ""
else
    echo "[3/6] .env already exists, skipping..."
fi

# Install systemd service for Flask backend
echo "[4/6] Installing PiMail systemd service..."
sudo cp pimail.service /etc/systemd/system/pimail.service
sudo systemctl daemon-reload
sudo systemctl enable pimail.service
sudo systemctl start pimail.service

# Create Chromium kiosk autostart
echo "[5/6] Setting up Chromium kiosk autostart..."
AUTOSTART_DIR="/home/$USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/pimail-browser.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=PiMail Browser
Exec=bash -c "sleep 5 && chromium --kiosk --noerrdialogs --disable-infobars --incognito --disable-translate --no-first-run http://localhost:5000"
X-GNOME-Autostart-enabled=true
EOF

cat > "$AUTOSTART_DIR/pimail-unclutter.desktop" << 'EOF'
[Desktop Entry]
Type=Application
Name=Hide Cursor
Exec=unclutter -idle 0.1
X-GNOME-Autostart-enabled=true
EOF

# Disable screen blanking
echo "[6/6] Disabling screen blanking..."
XSESSION_RC="/home/$USER/.xsessionrc"
if ! grep -q "xset s off" "$XSESSION_RC" 2>/dev/null; then
    cat >> "$XSESSION_RC" << 'EOF'
xset s off
xset -dpms
xset s noblank
EOF
fi

echo ""
echo "=== PiMail Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit your IMAP credentials: nano $PIMAIL_DIR/.env"
echo "  2. Reboot to start the dashboard: sudo reboot"
echo ""
echo "To check status:  sudo systemctl status pimail"
echo "To view logs:     journalctl -u pimail -f"
