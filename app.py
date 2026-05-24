from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
from collections import defaultdict

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

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {**HEADERS, "Accept": "application/vnd.github.v3.raw"}
    response = requests.get(url, headers=headers)
    return response.text if response.status_code == 200 else ""

def get_topics(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/topics"
    headers = {**HEADERS, "Accept": "application/vnd.github.mercy-preview+json"}
    response = requests.get(url, headers=headers)
    return response.json().get("names", []) if response.status_code == 200 else []

def get_similar_repos(topics, language):
    query = ""
    if topics:
        query = "+".join(topics[:2])
    elif language:
        query = f"language:{language}"
    else:
        return []

    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []

    items = response.json().get("items", [])
    return [
        {
            "name": r["full_name"],
            "url": r["html_url"],
            "stars": r["stargazers_count"],
            "description": r.get("description", ""),
            "language": r.get("language", "")
        }
        for r in items
    ]

def get_commit_history(commits):
    monthly = defaultdict(int)
    for commit in commits:
        try:
            date_str = commit["commit"]["author"]["date"]
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            key = date.strftime("%Y-%m")
            monthly[key] += 1
        except:
            continue

    sorted_months = sorted(monthly.keys())[-12:]
    return {
        "labels": sorted_months,
        "values": [monthly[m] for m in sorted_months]
    }

def analyze_code_quality(contents, owner, repo):
    issues = []
    good = []

    file_names = [f["name"].lower() for f in contents if isinstance(f, dict)]
    all_names = [f["name"] for f in contents if isinstance(f, dict)]

    # Check for test folder
    if any("test" in f for f in file_names):
        good.append("✅ Has tests folder — great practice!")
    else:
        issues.append("❌ No tests folder found — add unit tests")

    # Check for CI/CD
    if any(".github" in f for f in file_names) or any("workflow" in f for f in file_names):
        good.append("✅ CI/CD workflows detected")
    else:
        issues.append("❌ No CI/CD setup — consider adding GitHub Actions")

    # Check for docker
    if any("dockerfile" in f for f in file_names) or any("docker-compose" in f for f in file_names):
        good.append("✅ Docker support found")
    else:
        issues.append("⚠️ No Docker setup — consider containerizing")

    # Check for config files
    if any(f in file_names for f in [".env.example", ".env.sample"]):
        good.append("✅ Environment template file found")
    else:
        issues.append("⚠️ Add .env.example for contributors")

    # Check for package files
    if any(f in file_names for f in ["package.json", "requirements.txt", "pom.xml", "go.mod"]):
        good.append("✅ Dependency file found")
    else:
        issues.append("❌ No dependency file detected")

    return {"issues": issues, "good": good}

def score_readme(readme_text):
    if not readme_text:
        return 0, ["❌ No README found"]

    score = 0
    feedback = []

    if len(readme_text) > 500:
        score += 20
        feedback.append("✅ README has good length")
    else:
        feedback.append("❌ README is too short — add more detail")

    sections = ["installation", "usage", "contributing", "license", "features"]
    found = [s for s in sections if s in readme_text.lower()]
    score += len(found) * 10
    if found:
        feedback.append(f"✅ Found sections: {', '.join(found)}")
    missing = [s for s in sections if s not in readme_text.lower()]
    if missing:
        feedback.append(f"⚠️ Missing sections: {', '.join(missing)}")

    if "```" in readme_text:
        score += 10
        feedback.append("✅ Has code examples")
    else:
        feedback.append("⚠️ Add code examples to README")

    if "![" in readme_text or "badge" in readme_text.lower():
        score += 10
        feedback.append("✅ Has images or badges")
    else:
        feedback.append("⚠️ Add badges or screenshots")

    if "#" in readme_text:
        score += 10
        feedback.append("✅ Has proper headings")

    return min(score, 100), feedback

def calculate_scores(repo_data, languages, commits, contents, readme_text):
    scores = {}

    doc_score = 0
    file_names = [f["name"].lower() for f in contents if isinstance(f, dict)]
    if any("readme" in f for f in file_names): doc_score += 40
    if any("license" in f for f in file_names): doc_score += 20
    if any("contributing" in f for f in file_names): doc_score += 20
    if repo_data.get("description"): doc_score += 20
    scores["documentation"] = min(doc_score, 100)

    activity_score = 0
    if len(commits) > 50: activity_score = 100
    elif len(commits) > 20: activity_score = 75
    elif len(commits) > 10: activity_score = 50
    elif len(commits) > 3: activity_score = 30
    else: activity_score = 10
    scores["activity"] = activity_score

    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    watchers = repo_data.get("watchers_count", 0)
    community_score = min((stars * 2 + forks * 3 + watchers), 100)
    scores["community"] = community_score

    lang_count = len(languages)
    if lang_count >= 5: scores["tech_diversity"] = 100
    elif lang_count == 4: scores["tech_diversity"] = 80
    elif lang_count == 3: scores["tech_diversity"] = 60
    elif lang_count == 2: scores["tech_diversity"] = 40
    else: scores["tech_diversity"] = 20

    readme_score, _ = score_readme(readme_text)
    scores["readme_quality"] = readme_score

    scores["overall"] = int(
        scores["documentation"] * 0.25 +
        scores["activity"] * 0.25 +
        scores["community"] * 0.15 +
        scores["tech_diversity"] * 0.15 +
        scores["readme_quality"] * 0.20
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
    readme_text = get_readme(owner, repo)
    topics = get_topics(owner, repo)

    primary_language = repo_data.get("language", "")
    similar_repos = get_similar_repos(topics, primary_language)
    commit_history = get_commit_history(commits)
    code_quality = analyze_code_quality(contents, owner, repo)
    readme_score, readme_feedback = score_readme(readme_text)
    scores = calculate_scores(repo_data, languages, commits, contents, readme_text)
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
            "topics": topics,
        },
        "languages": languages,
        "commit_count": len(commits),
        "commit_history": commit_history,
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
        "verdict_color": verdict_color,
        "code_quality": code_quality,
        "readme_feedback": readme_feedback,
        "similar_repos": similar_repos
    }

    return jsonify(result)

@app.route("/compare", methods=["POST"])
def compare():
    data = request.get_json()
    url1 = data.get("url1", "")
    url2 = data.get("url2", "")

    results = []
    for url in [url1, url2]:
        owner, repo = parse_repo_url(url)
        if not owner or not repo:
            return jsonify({"error": f"Invalid URL: {url}"}), 400

        repo_data = get_repo_data(owner, repo)
        if not repo_data:
            return jsonify({"error": f"Repo not found: {url}"}), 404

        languages = get_languages(owner, repo)
        commits = get_commits(owner, repo)
        contents = get_contents(owner, repo)
        readme_text = get_readme(owner, repo)
        scores = calculate_scores(repo_data, languages, commits, contents, readme_text)
        verdict, verdict_color = get_verdict(scores["overall"])

        results.append({
            "repo": {
                "name": repo_data.get("name"),
                "full_name": repo_data.get("full_name"),
                "description": repo_data.get("description"),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "url": repo_data.get("html_url"),
                "open_issues": repo_data.get("open_issues_count", 0),
            },
            "languages": languages,
            "commit_count": len(commits),
            "scores": scores,
            "verdict": verdict,
            "verdict_color": verdict_color
        })

    return jsonify({"repos": results})

@app.route("/profile", methods=["POST"])
def profile():
    data = request.get_json()
    username = data.get("username", "").replace("https://github.com/", "").strip("/")

    user_url = f"https://api.github.com/users/{username}"
    user_res = requests.get(user_url, headers=HEADERS)
    if user_res.status_code != 200:
        return jsonify({"error": "User not found"}), 404

    user = user_res.json()

    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    repos_res = requests.get(repos_url, headers=HEADERS)
    repos = repos_res.json() if repos_res.status_code == 200 else []

    all_languages = defaultdict(int)
    total_stars = 0
    total_forks = 0
    top_repos = []

    for r in repos:
        if isinstance(r, dict):
            total_stars += r.get("stargazers_count", 0)
            total_forks += r.get("forks_count", 0)
            lang = r.get("language")
            if lang:
                all_languages[lang] += 1
            top_repos.append({
                "name": r.get("name"),
                "url": r.get("html_url"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language", ""),
                "description": r.get("description", "")
            })

    top_repos = sorted(top_repos, key=lambda x: x["stars"], reverse=True)[:6]

    activity_score = min(len(repos) * 2, 100)
    star_score = min(total_stars * 2, 100)
    diversity_score = min(len(all_languages) * 15, 100)
    overall = int((activity_score + star_score + diversity_score) / 3)

    return jsonify({
        "user": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar": user.get("avatar_url"),
            "bio": user.get("bio"),
            "location": user.get("location"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "public_repos": user.get("public_repos"),
            "url": user.get("html_url"),
            "created_at": user.get("created_at"),
        },
        "stats": {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "languages": dict(all_languages),
            "repo_count": len(repos),
        },
        "scores": {
            "activity": activity_score,
            "popularity": star_score,
            "diversity": diversity_score,
            "overall": overall
        },
        "top_repos": top_repos
    })

if __name__ == "__main__":
    app.run(debug=True)
    # DevLens - GitHub Repository Analyzer
