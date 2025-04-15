#!/bin/bash

# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx

# Create application directory
sudo mkdir -p /var/www/photo-share
sudo chown $USER:$USER /var/www/photo-share

# Clone the repository
git clone https://github.com/avarabey/oneshowphoto.git /var/www/photo-share

# Setup virtual environment
cd /var/www/photo-share
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/photo-share.service << EOF
[Unit]
Description=Photo Share Application
After=network.target

[Service]
User=$USER
WorkingDirectory=/var/www/photo-share
Environment="PATH=/var/www/photo-share/venv/bin"
ExecStart=/var/www/photo-share/venv/bin/python app.py

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/photo-share << EOF
server {
    listen 80;
    server_name varabey.online;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443;
    server_name varabey.online;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the Nginx site
sudo ln -s /etc/nginx/sites-available/photo-share /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Start and enable services
sudo systemctl start photo-share
sudo systemctl enable photo-share
sudo systemctl restart nginx

echo "Installation complete!"