# Move your script (assuming it's named maintainer.sh)

sudo cp ~/Desktop/arazim_local/maintainer.sh /usr/local/bin/wifi-maintainer.sh

# Make sure it's executable

sudo chmod +x /usr/local/bin/wifi-maintainer.sh

::/etc/systemd/system/wifi-maintainer.service::

[Unit]
Description=Maintain Dual NIC Connections (G2 and Printer)
After=NetworkManager.service

[Service]

# Run as root to ensure nmcli has full permissions

Type=simple
ExecStart=/usr/local/bin/wifi-maintainer.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

###

# 1. Tell systemd to reload its configuration and find your new service

sudo systemctl daemon-reload

# 2. Set the service to start automatically on every boot

sudo systemctl enable wifi-maintainer.service

# 3. Start the service immediately

sudo systemctl start wifi-maintainer.service
