if ! grep -q "deb http://ftp.debian.org/debian stable main" /etc/apt/sources.list; then
  echo "deb http://ftp.debian.org/debian stable main" >> /etc/apt/sources.list
fi
apt update && apt install -y sqlite3

gunicorn --bind=0.0.0.0 --timeout 600 app:app