import mysql.connector

config = {
    'user': 'data_user',
    'password': 'YKJdqLzYDqLsLwK43HA4B5TPGEO',
    'host': 'aviation.esterling.cloud',
    'database': 'data_python',
    'port': 3306,
    'ssl_verify_cert': True,
    'connect_timeout': 10
}

try:
    connection = mysql.connector.connect(**config)
    print("Connection successful!")
except mysql.connector.Error as err:
    print(f"Error: {err}")