import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host='aviation.esterling.cloud',
        user='data_user',
        password='YKJdqLzYDqLsLwK43HA4B5TPGEO',
        database='data_python',
        port=3306
    )

    if connection.is_connected():
        db_info = connection.get_server_info()
        print("Successfully connected to MySQL Server version ", db_info)
        
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record[0])

except Error as e:
    print("Error while connecting to MySQL", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")