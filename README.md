**How to setup vps**
sudo apt-get update
sudo apt-get install docker.io -y
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo apt-get install git -y
git clone https://github.com/Bunnarin/django-rbac-ums.git
cd django-rbac-ums
nano .env
sudo docker-compose run --rm certbot /app/certbot_init.sh
sudo docker-compose down
sudo docker-compose up