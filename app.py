from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def parse_repo_url(url):
    url = url.strip().rstrip("/")
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None

def get_repo_data(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else None

def get_languages(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else {}

def get_commits(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

def get_contents(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=10"
    response = requests.get(url, headers=HEADERS)
    return response.json() if response.status_code == 200 else []

def calculate_scores(repo_data, languages, commits, contents):
    scores = {}

    # Documentation score
    doc_score = 0
    file_names = [f["name"].lower() for f in contents if isinstance(f, dict)]
    if any("readme" in f for f in file_names): doc_score += 40
    if any("license" in f for f in file_names): doc_score += 20
    if any("contributing" in f for f in file_names): doc_score += 20
    if repo_data.get("description"): doc_score += 20
    scores["documentation"] = min(doc_score, 100)

    # Activity score
    activity_score = 0
    if len(commits) > 50: activity_score = 100
    elif len(commits) > 20: activity_score = 75
    elif len(commits) > 10: activity_score = 50
    elif len(commits) > 3: activity_score = 30
    else: activity_score = 10
    scores["activity"] = activity_score

    # Community score
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    watchers = repo_data.get("watchers_count", 0)
    community_score = min((stars * 2 + forks * 3 + watchers), 100)
    scores["community"] = community_score

    # Tech diversity score
    lang_count = len(languages)
    if lang_count >= 5: scores["tech_diversity"] = 100
    elif lang_count == 4: scores["tech_diversity"] = 80
    elif lang_count == 3: scores["tech_diversity"] = 60
    elif lang_count == 2: scores["tech_diversity"] = 40
    else: scores["tech_diversity"] = 20

    # Overall score
    scores["overall"] = int(
        scores["documentation"] * 0.3 +
        scores["activity"] * 0.3 +
        scores["community"] * 0.2 +
        scores["tech_diversity"] * 0.2
    )

    return scores

def get_verdict(overall_score):
    if overall_score >= 80: return "Excellent", "#00c853"
    elif overall_score >= 60: return "Good", "#64dd17"
    elif overall_score >= 40: return "Average", "#ffd600"
    elif overall_score >= 20: return "Needs Work", "#ff6d00"
    else: return "Abandon Ship", "#d50000"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    repo_url = data.get("url", "")

    owner, repo = parse_repo_url(repo_url)
    if not owner or not repo:
        return jsonify({"error": "Invalid GitHub URL"}), 400

    repo_data = get_repo_data(owner, repo)
    if not repo_data:
        return jsonify({"error": "Repository not found"}), 404

    languages = get_languages(owner, repo)
    commits = get_commits(owner, repo)
    contents = get_contents(owner, repo)
    contributors = get_contributors(owner, repo)

    scores = calculate_scores(repo_data, languages, commits, contents)
    verdict, verdict_color = get_verdict(scores["overall"])

    result = {
        "repo": {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "watchers": repo_data.get("watchers_count", 0),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "url": repo_data.get("html_url"),
            "open_issues": repo_data.get("open_issues_count", 0),
            "default_branch": repo_data.get("default_branch"),
            "size": repo_data.get("size", 0),
        },
        "languages": languages,
        "commit_count": len(commits),
        "contributors": [
            {
                "login": c.get("login"),
                "avatar": c.get("avatar_url"),
                "contributions": c.get("contributions"),
                "url": c.get("html_url")
            } for c in contributors if isinstance(c, dict)
        ],
        "scores": scores,
        "verdict": verdict,
        "verdict_color": verdict_color
    }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)