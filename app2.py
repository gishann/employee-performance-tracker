import pyodbc
import requests

# Replace these values with your GitHub username and access token
github_username = "gishann"
github_token = "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"

# Replace these values with your Amazon RDS SQL Server database credentials
db_config = {
    'server': 'employee-performance.cv8lifo4uls5.us-east-2.rds.amazonaws.com',
    'database': 'employee_performance',
    'user': 'admin',
    'password': 'user1234',
    'driver': '{ODBC Driver 17 for SQL Server}',  # Make sure to have the correct driver installed
}

# Function to make authenticated requests to the GitHub API with rate limiting
def github_api_request(endpoint, params=None):
    base_url = "https://api.github.com"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }
    try:
        response = requests.get(f"{base_url}/{endpoint}", params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"GitHub API request error: {e}")
        return None

# Function to establish a connection to the SQL Server database
def get_db_connection():
    try:
        connection = pyodbc.connect(
            'DRIVER=' + db_config['driver'] + ';SERVER=' + db_config['server'] + ';DATABASE=' + db_config['database'] +
            ';UID=' + db_config['user'] + ';PWD=' + db_config['password'])
        print("Connected to the database.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to insert metrics into the database for a single contributor
def insert_metrics(cursor, username, repo_owner, repo_name):
    commits = get_total_commits(username, repo_owner, repo_name)
    open_issues = get_open_issues(username, repo_owner, repo_name)
    pull_requests = get_pull_requests(username, repo_owner, repo_name)

    # Insert new data
    insert_query = "INSERT INTO metrics (username, repo_owner, repo_name, commits, open_issues, pull_requests) VALUES (?, ?, ?, ?, ?, ?)"
    insert_values = (username, repo_owner, repo_name, commits, open_issues, pull_requests)

    try:
        cursor.execute(insert_query, insert_values)
        print(f"Metrics for {username} inserted successfully.")
    except Exception as e:
        print(f"Error inserting metrics for {username}: {e}")

# Metric 1: Total number of commits by a user in a repository
def get_total_commits(username, repo_owner, repo_name):
    endpoint = f"repos/{repo_owner}/{repo_name}/commits"
    params = {"author": username}
    all_commits = get_all_items(endpoint, params=params)
    total_commits = len(all_commits)
    return total_commits

# Metric 2: Number of open issues assigned to a user in a repository
def get_open_issues(username, repo_owner, repo_name):
    endpoint = f"repos/{repo_owner}/{repo_name}/issues"
    params = {"assignee": username, "state": "open"}
    all_issues = get_all_items(endpoint, params=params)
    open_issues_count = len(all_issues)
    return open_issues_count

# Metric 3: Number of pull requests created by a user in a repository
def get_pull_requests(username, repo_owner, repo_name):
    endpoint = f"repos/{repo_owner}/{repo_name}/pulls"
    params = {"state": "all", "creator": username}
    all_pull_requests = get_all_items(endpoint, params=params)
    pull_requests_count = len(all_pull_requests)
    return pull_requests_count

# Function to handle pagination and get all items
def get_all_items(endpoint, params=None):
    params = params or {}
    all_items = []
    page = 1
    while True:
        params["page"] = page
        response = github_api_request(endpoint, params=params)
        if not response:
            break
        all_items.extend(response)
        page += 1
        if page > 10:  # Set a maximum of 10 pages to avoid potential infinite loops
            print("Exceeded maximum number of pages.")
            break
    return all_items

# Establish the database connection
connection = get_db_connection()
if not connection:
    # Handle the case where the database connection cannot be established
    exit()

try:
    # Create a cursor
    cursor = connection.cursor()

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

    # Example usage
    repo_owner = "bistecglobal"
    repo_name = "blockchain-certificates-issuer"
    contributors_endpoint = f"repos/{repo_owner}/{repo_name}/contributors"
    contributors = get_all_items(contributors_endpoint)

    # Process contributors sequentially
    for contributor in contributors:
        insert_metrics(cursor, contributor['login'], repo_owner, repo_name)

finally:
    # Close the cursor and the database connection
    cursor.close()
    connection.close()
