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
    cursor = connection.cursor()

    # Get all tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("\n=== Available Tables ===")
    for table in tables:
        table_name = table[0]
        print(f"\n--- Table: {table_name} ---")
        
        # Get table content
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        for row in rows:
            print(row)
        print("\n")
except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("Database connection closed.")