import requests
import pyodbc
from datetime import datetime, timedelta

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
            'DRIVER=' + db_config['driver'] + ';SERVER=' + db_config['server'] + ';DATABASE=' + db_config[
                'database'] + ';UID=' + db_config['user'] + ';PWD=' + db_config['password'])
        print("Connected to the database.")
        return connection
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Function to insert or update metrics into the database for a single contributor
def insert_metrics(username, repo_owner, repo_name):
    commits = get_total_commits(username, repo_owner, repo_name)
    open_issues = get_open_issues(username, repo_owner, repo_name)
    pull_requests = get_pull_requests(username, repo_owner, repo_name)
    time_since_last_commit = get_time_since_last_commit(username, repo_owner, repo_name)

    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    # Check if data for the user and repository already exists
    existing_data_query = "SELECT * FROM metrics WHERE username = ? AND repo_owner = ? AND repo_name = ?"
    existing_data_values = (username, repo_owner, repo_name)

    try:
        cursor.execute(existing_data_query, existing_data_values)
        existing_data = cursor.fetchone()

        if existing_data:
            # User exists, check if data has changed before performing an update
            existing_commits, existing_open_issues, existing_pull_requests, existing_time_since_last_commit = existing_data[3:7]

            if (
                existing_commits != commits or
                existing_open_issues != open_issues or
                existing_pull_requests != pull_requests or
                existing_time_since_last_commit != time_since_last_commit
            ):
                # Update data if it has changed
                update_query = """
                    UPDATE metrics
                    SET commits = ?, open_issues = ?, pull_requests = ?, time_since_last_commit = ?
                    WHERE username = ? AND repo_owner = ? AND repo_name = ?
                """
                update_values = (commits, open_issues, pull_requests, time_since_last_commit, username, repo_owner, repo_name)

                cursor.execute(update_query, update_values)
                connection.commit()
                print(f"Metrics for {username} updated successfully.")
            else:
                print(f"Metrics for {username} in {repo_owner}/{repo_name} already up to date. No changes.")
        else:
            # User doesn't exist, insert new data
            insert_query = "INSERT INTO metrics (username, repo_owner, repo_name, commits, open_issues, pull_requests, time_since_last_commit) VALUES (?, ?, ?, ?, ?, ?, ?)"
            insert_values = (username, repo_owner, repo_name, commits, open_issues, pull_requests, time_since_last_commit)

            cursor.execute(insert_query, insert_values)
            connection.commit()
            print(f"Metrics for {username} inserted successfully.")
    except Exception as e:
        print(f"Error inserting/updating metrics for {username}: {e}")
    finally:
        cursor.close()
        connection.close()

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

# Metric 4: Time since the last commit by a user in a repository
def get_time_since_last_commit(username, repo_owner, repo_name):
    endpoint = f"repos/{repo_owner}/{repo_name}/commits"
    params = {"author": username}
    all_commits = get_all_items(endpoint, params=params)
    if all_commits:
        last_commit_date = datetime.strptime(all_commits[0]['commit']['committer']['date'], "%Y-%m-%dT%H:%M:%SZ")
        time_since_last_commit = datetime.utcnow() - last_commit_date
        return time_since_last_commit.days
    else:
        return None

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

# Example usage
repo_owner = "facebookresearch"
repo_name = "seamless_communication"
contributors_endpoint = f"repos/{repo_owner}/{repo_name}/contributors"
contributors = get_all_items(contributors_endpoint)

# Iterate through contributors and insert/update metrics into the database
for contributor in contributors:
    username = contributor['login']

    # Insert or update metrics into the database for each contributor
    insert_metrics(username, repo_owner, repo_name)
