from flask import Flask, render_template, redirect, url_for
import pyodbc
from app2 import insert_metrics, get_all_items

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

@app.route('/refresh')
def refresh_data():
    # Your GitHub repository information
    repo_owner = "bistecglobal"
    repo_name = "blockchain-certificates-issuer"

    # Fetch contributors from GitHub
    contributors_endpoint = f"repos/{repo_owner}/{repo_name}/contributors"
    contributors = get_all_items(contributors_endpoint)

    # Establish a connection to the database
    connection = get_db_connection()

    if not connection:
        return "Error connecting to the database."

    cursor = connection.cursor()

    try:
        # Drop existing table
        drop_table_query = "DROP TABLE IF EXISTS metrics"
        cursor.execute(drop_table_query)
        print("Dropped existing table.")

        # Create a new table
        create_table_query = """
            CREATE TABLE metrics (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(255),
                repo_owner NVARCHAR(255),
                repo_name NVARCHAR(255),
                commits INT,
                open_issues INT,
                pull_requests INT
            )
        """
        cursor.execute(create_table_query)
        print("Created new table.")

        # Iterate through contributors and insert metrics into the database
        for contributor in contributors:
            username = contributor['login']
            insert_metrics(cursor, username, repo_owner, repo_name)

        connection.commit()

    except Exception as e:
        connection.rollback()
        print(f"Error refreshing data: {e}")
        return "Error refreshing data."
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('index'))

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
        return "Error fetching data from the database."
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
