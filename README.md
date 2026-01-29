# Adaptive Placement Preparation System 

## 📌 Project Overview
This project is for a real-time adaptive learning platform designed for college placement preparation. It uses a **Skill Drift Detection** algorithm to continuously analyze student performance. If a student struggles or takes too long to answer, the system detects "drift," lowers the difficulty, and provides personalized, context-aware explanations (simulated RAG pipeline).

## 🚀 Tech Stack
* **Frontend:** React.js, Tailwind CSS, Axios
* **Backend:** Python, FastAPI
* **Database:** (Mocked) In-memory Python lists for PoC
* **AI/ML:** Scikit-learn logic for drift detection, simulated RAG responses

## ⚡ How to Run Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/adaptive-placement-system.git](https://github.com/YOUR_USERNAME/adaptive-placement-system.git)
cd adaptive-placement-system
```
### 2. Setup the Backend (Python/FastAPI)
Open a terminal in the project root:
```
cd backend
python -m venv .venv

```
### Activate virtual environment
### On Windows:
```
.venv\Scripts\activate

```
### On Mac/Linux:
```
source .venv/bin/activate

```
```
pip install -r requirements.txt
uvicorn main:app --reload

```

### 3. Setup the Frontend (React)
Open a new terminal window (keep the backend running):
```
cd frontend
npm install
npm start

```

