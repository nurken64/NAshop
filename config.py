import os

SECRET_KEY = os.environ.get('APP_SECRET_KEY')

DB_HOST = os.environ.get('DB_HOST', 'shopNA.mysql.pythonanywhere-services.com')
DB_USER = os.environ.get('DB_USER', 'shopNA')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password000')
DB_DATABASE = os.environ.get('DB_DATABASE', 'shopNA$back')


db_config = {
    'host': 'shopNA.mysql.pythonanywhere-services.com',
    'user': 'shopNA',
    'password': 'password000',
    'database': 'shopNA$back',
    'auth_plugin': 'mysql_native_password'
}
