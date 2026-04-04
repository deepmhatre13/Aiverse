# Aiverse

**ML Engineering Platform for Serious Developers**

> Train. Compete. Ship ML Systems.

[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://react.dev)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat&logo=django)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)](https://docker.com)

Live → [aiverse-webai.vercel.app](https://aiverse-webai.vercel.app)

---

## What is Aiverse?

Most ML platforms are either theory-heavy courses or competition-focused arenas like Kaggle. Neither teaches you to actually build and ship ML systems.

Aiverse sits in between:
```
Learn → Experiment → Solve → Improve → Repeat
```

One platform. Real execution. No fake outputs.

---

## Features

### ML Problems
Solve real ML challenges with actual datasets. Write code in the browser, submit, and get evaluated by a sandboxed backend executor — similar to LeetCode but for machine learning.

- Classification, regression, clustering problems
- In-browser code editor
- Docker-sandboxed execution
- Instant feedback and scoring
- ELO-based leaderboard ranking

### ML Playground
An interactive experimentation lab. No setup required.

1. Pick a dataset
2. Choose a model (Logistic Regression, Random Forest, SVM, KNN)
3. Tune hyperparameters
4. Train
5. Visualize accuracy, loss, confusion matrix

Designed for exploration, not just submission.

### AI Mentor
Ask any ML-related question and get a contextual explanation — not a generic answer. Currently improving personalization and user-awareness.

### Learn
Structured ML curriculum covering:
- Classification and regression
- Model evaluation metrics
- Overfitting and regularization
- Core algorithms with examples

### Discussions
Community Q&A. Share approaches, ask doubts, learn from others.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Tailwind CSS, Framer Motion |
| Backend | Django 4.2, Django REST Framework |
| Database | PostgreSQL |
| Async | Celery + Redis |
| Sandbox | Docker (isolated code execution) |
| ML | scikit-learn, pandas, NumPy |
| Deploy | Vercel (frontend), Render (backend) |

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for sandbox + Redis)
- PostgreSQL

### 1. Clone the repo
```bash
git clone https://github.com/deepmhatre13/Aiverse.git
cd Aiverse
```

### 2. Backend setup
```bash
cd aiverse_backend/backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in your values
python manage.py migrate
```

### 3. Start services
```bash
# Redis (via Docker)
docker run -p 6379:6379 redis

# Celery worker
celery -A backend worker --loglevel=info --pool=solo

# Django
python manage.py runserver
```

### 4. Frontend setup
```bash
cd aiverse_frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Environment Variables

Create a `.env` file in `aiverse_backend/backend/`:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgresql://postgres:password@localhost:5432/aiverse_db
REDIS_URL=redis://localhost:6379/0
```

---



---

## What Makes It Different

| Typical Student Projects | Aiverse |
|---|---|
| Static UI demos | Real backend execution |
| Hardcoded ML outputs | Live pipeline runs in Docker |
| Disconnected modules | Integrated learn → solve → improve loop |
| No evaluation logic | Actual scoring against ground truth |

---

## Current Limitations

Being honest about where it stands:

- Mentor responses are not deeply personalized yet
- Playground uses static datasets
- No experiment history or comparison across runs
- Modules are loosely connected (improving)

---

## Roadmap

- [ ] User intelligence layer — track patterns, surface insights
- [ ] Experiment history and side-by-side comparison
- [ ] Personalized problem recommendations
- [ ] Smarter mentor with user context awareness
- [ ] More problem types (NLP, time series, CV)

---

## Deployment

| Service | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Render PostgreSQL |
| Redis | Render Redis |

---
