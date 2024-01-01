from flask import Flask, render_template
import pyodbc

app = Flask(__name__)

# Replace these values with your database credentials
db_config = {
    'server': 'employee-performance.cv8lifo4uls5.us-east-2.rds.amazonaws.com',
    'database': 'employee_performance',
    'user': 'admin',
    'password': 'user1234',
    'driver': '{ODBC Driver 17 for SQL Server}',
}

def get_db_connection():
    try:
        connection = pyodbc.connect(
            'DRIVER=' + db_config['driver'] + ';SERVER=' + db_config['server'] + ';DATABASE=' + db_config['database'] +
            ';UID=' + db_config['user'] + ';PWD=' + db_config['password'])
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route('/')
def index():
    connection = get_db_connection()

    if not connection:
        return "Error connecting to the database."

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT * FROM metrics")
        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        return render_template('index.html', columns=columns, data=data)
    except Exception as e:
        print(f"Error fetching data from the database: {e}")
        return f"Error fetching data from the database: {e}"
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

#test