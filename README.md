## Web server
```bash
uvicorn app.main:app --reload
```


## Postgres
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
sudo -i -u postgres
psql
```
### Create db
```bash
CREATE DATABASE mydatabase;
CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;
```
### Connection
```bash
psql -U evalshine -d hotels_db
```


## Migrations
```bash
alembic init -t async app/migrations
```
### edit `app/migrations/env.py`
```python
from alembic import context
#------------------------------
<PASTE CODE BELOW HERE>
#------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
```
```python
from app.config import settings
from app.database.db import Base
from app.models.hotels import HotelsOrm
from app.models.rooms import RoomsOrm
from app.models.users import UsersOrm

config = context.config

config.set_main_option("sqlalchemy.url", f"{settings.DB_URL}")

target_metadata = Base.metadata
```
### generate and upgrade
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Redis
```bash
sudo systemctl start redis-server
sudo systemctl status redis-server
```

## Celery
```bash
celery -A app.tasks.celery_app.celery_instance worker --loglevel=info
```

## Celery Beat
```bash
celery -A app.tasks.celery_app.celery_instance beat --loglevel=info
```

## Testing
```bash
pip3 install pytest
pip3 install pytest-dotenv
pip3 install pytest-asyncio
```

### Test db
```bash
psql -U evalshine -d hotels_db_test
```


## Docker
```bash
docker network create myNetwork

docker run --name booking_db \
    -p 6432:5432 \
    -e POSTGRES_USER=evalshine \
    -e POSTGRES_PASSWORD=docent1315 \
    -e POSTGRES_DB=booking \
    --network=myNetwork \
    --rm \
    --volume pg-data:/var/lib/postgresql/data \
    -d postgres:16

docker run --name booking_cache \
    -p 7379:6379 \
    --network=myNetwork \
    --rm \
    -d redis:7.4


docker build -t fastapi .

docker run --name booking_back \
    -p 7777:8000 \
    --network=myNetwork \
    fastapi


docker run --name booking_celery_worker \
    --network=myNetwork \
    fastapi \
    celery -A app.tasks.celery_app.celery_instance worker --loglevel=info


docker run --name booking_celery_beat \
    --network=myNetwork \
    fastapi \
    celery -A app.tasks.celery_app.celery_instance beat --loglevel=info


docker run --name booking_nginx \
    --volume ./nginx.conf:/etc/nginx/nginx.conf \
    --network=myNetwork \
    --rm -p 80:80 -d nginx
```

## Nginx DDOS
```nginx.conf
events {}

http {
    limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;

    server {
        location / {
            limit_req zone=mylimit;
            proxy_pass http://booking_back:8000/;
        }
    }
}
```

## Docker compose
```bash
docker compose build
docker compose up -d
```

## Gitlab
- Create project
### Add remote to gitlab
- git remote add gitlab https://gitlab.com/username/new-repo.git
- git push gitlab main
- git pull gitlab main
- git remote -v (all remotes)


## VPS - adminvps
```bash
ssh username@server_ip
```
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```
- Add ssh key to gitlab
### Install git
```bash
sudo apt-get update
sudo apt-get install git
```
## Install Docker
```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```
```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Domain 
- https://cp.hoster.by/domains/715624/dns/hosting - hotelsapi.xyz
- Add dns servers: ns1.adminvps.ru, ns2.adminvps.net
- https://my.adminvps.ru/index.php?m=DNSManager2 - add domain and ip from vps

## SSL
### Generate
- sudo apt-get install snapd
- sudo snap install --classic certbot
- sudo apt-get install nginx
- stop docker nginx
- systemctl start nginx
- sudo certbot certonly --nginx
- enter email, domain
- systemctl stop nginx
- run docker nginx
### Update
- stop docker nginx
- systemctl start nginx
- certbot renew --force-renewal
- systemctl stop nginx
- run docker nginx
### nginx.conf example
```nginx.conf
events {}

http {
    server {
        listen 443 ssl;

        location / {
            proxy_pass http://booking_back:8000/;
        }

        ssl_certificate /etc/letsencrypt/live/hotelsapi.xyz/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/hotelsapi.xyz/privkey.pem;
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }
}
```
### Run ssl nginx
- create file nginx.conf in vps
```bash
docker run --name booking_nginx \
    --volume /root/nginx.conf:/etc/nginx/nginx.conf \
    --volume /etc/letsencrypt:/etc/letsencrypt \
    --volume /var/lib/letsencrypt:/var/lib/letsencrypt \
    --network=myNetwork \
    --rm -p 443:443 -d nginx
```

## Site
- https://hotelsapi.xyz

## CI/CD
```bash
docker run -d --name gitlab-runner --restart always \
  -v /srv/gitlab-runner/config:/etc/gitlab-runner \
  -v /var/run/docker.sock:/var/run/docker.sock \
  gitlab/gitlab-runner:alpine
```
- settings ci/cd
- disable instance runner
- new project runner
- run unsagged jobs
- create runner
```bash
docker run --rm -it \
    -v /srv/gitlab-runner/config:/etc/gitlab-runner \
    gitlab/gitlab-runner:alpine register
```
- enter url
- enter token
- name - enter
- enter docker
- enter docker:dind
- nano /srv/gitlab-runner/config/config.toml
- volumes = ["/cache"] меняем на volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
- Gitlab build - pipelines
- try teplate - commit
- git pull gitlab main
### Add end in gitlab
- Settings -> ci/cd -> variables

## Docker compose local
- sudo docker build -t hotelsapi .
- sudo docker compose -f docker-compose-local.yml up -d
- docker image prune -f (delete all <none> images)

## Media files
- create media path in vps