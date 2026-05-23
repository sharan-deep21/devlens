# 🔍 DevLens — GitHub Repository Analyzer

> Instantly analyze any GitHub repository and get deep insights on code quality, activity, documentation, and community health.

![DevLens Banner](https://img.shields.io/badge/DevLens-GitHub%20Analyzer-58a6ff?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask)
![JavaScript](https://img.shields.io/badge/JavaScript-Frontend-yellow?style=for-the-badge&logo=javascript)

## 🚀 Live Demo

👉 **[Try DevLens Live](https://devlens.onrender.com)**

---

## 📸 What It Does

Paste any GitHub repository URL and DevLens instantly gives you:

- 📊 **Health Scores** — Documentation, Activity, Community, Tech Diversity, README Quality
- 🏆 **Overall Verdict** — From "Excellent" to "Abandon Ship"
- 🌐 **Language Breakdown** — Beautiful donut chart with percentages
- 👥 **Contributors** — Top contributors with avatars
- 📈 **Repository Stats** — Stars, Forks, Commits, Issues
- 📋 **Repo Info** — Created date, last updated, size, branch
- 📉 **Commit History Graph** — Monthly commit activity chart
- 🔍 **Code Quality Analysis** — Detects tests, CI/CD, Docker, env files
- 📝 **README Scorer** — Analyzes your README quality with feedback
- 🔗 **Similar Repos** — Suggests related repositories
- ⚔️ **Compare Two Repos** — Side by side comparison with winner highlights
- 👤 **GitHub Profile Analyzer** — Full developer scorecard with top repos

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python, Flask |
| API | GitHub REST API v3 |
| Deployment | Render (Backend) |

---

## ⚙️ Run Locally

**1. Clone the repository**
```bash
git clone https://github.com/sharan-deep21/devlens.git
cd devlens
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create `.env` file**
```bash
GITHUB_TOKEN=your_github_token_here
```

**5. Run the app**
```bash
python app.py
```

**6. Open in browser**