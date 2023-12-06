import requests
from datetime import datetime, timedelta

# Replace these values with your GitHub username and access token
github_username = "gishann"
github_token = "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"

# Function to make authenticated requests to the GitHub API
def github_api_request(endpoint, params=None):
    base_url = "https://api.github.com"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }
    response = requests.get(f"{base_url}/{endpoint}", params=params, headers=headers)
    return response.json()

# Function to handle pagination and get all items
def get_all_items(endpoint, params=None):
    params = params or {}  # Initialize params as an empty dictionary if it's None
    all_items = []
    page = 1
    while True:
        params["page"] = page
        response = github_api_request(endpoint, params=params)
        if not response:
            break
        all_items.extend(response)
        page += 1
    return all_items

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

# Get the list of contributors to the repository
repo_owner = "facebookresearch"
repo_name = "seamless_communication"
contributors_endpoint = f"repos/{repo_owner}/{repo_name}/contributors"
contributors = get_all_items(contributors_endpoint)

# Iterate through contributors and collect metrics
for contributor in contributors:
    username = contributor['login']
    commits = get_total_commits(username, repo_owner, repo_name)
    open_issues = get_open_issues(username, repo_owner, repo_name)
    pull_requests = get_pull_requests(username, repo_owner, repo_name)
    time_since_last_commit = get_time_since_last_commit(username, repo_owner, repo_name)

    print(f"\nMetrics for contributor {username}:")
    print(f"Total Commits: {commits}")
    print(f"Open Issues assigned: {open_issues}")
    print(f"Pull Requests created: {pull_requests}")
    print(f"Time Since Last Commit: {time_since_last_commit} days")
