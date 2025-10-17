# Python script to install on STUN server
This script must be installed on STUN server.
Be sure to copy content of this folder into /opt/udpCnrRelay on STUN server and not NBI.

# Installation
    cd /opt
    python -m venv udpCnrRelay
    cd udpCnrRelay
    cp /opt/genieacs/python/* .
    source bin/activate
    pip install --no-cache-dir -r requirements.txt
    cp stun-relay.service /etc/systemd/system
    systemctl enable stun-relay.service
    systemctl start stun-relay.service
