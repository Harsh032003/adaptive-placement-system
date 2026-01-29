# Adaptive Placement Preparation System 

## 📌 Project Overview
This project is a Proof of Concept (PoC) for a real-time adaptive learning platform designed for college placement preparation. It uses a **Skill Drift Detection** algorithm to continuously analyze student performance. If a student struggles or takes too long to answer, the system detects "drift," lowers the difficulty, and provides personalized, context-aware explanations (simulated RAG pipeline).

## 🚀 Tech Stack
* **Frontend:** React.js, Tailwind CSS, Axios
* **Backend:** Python, FastAPI
* **Database:** (Mocked) In-memory Python lists for PoC
* **AI/ML:** Scikit-learn logic for drift detection, simulated RAG responses

## 📂 Folder Structure


adaptive-placement-system/
├── backend/
│   ├── .venv/                 # Python Virtual Environment (ignored in git)
│   ├── main.py                # Core Logic (FastAPI, Drift Detection, Mock RAG)
│   └── requirements.txt       # Python dependencies (fastapi, uvicorn, pydantic)
│
├── frontend/
│   ├── node_modules/          # React dependencies (ignored in git)
│   ├── public/
│   │   └── index.html         # Entry HTML (Tailwind CSS CDN added here)
│   ├── src/
│   │   ├── App.jsx            # Main Dashboard & Login Logic
│   │   └── index.js           # React DOM rendering
│   ├── package.json           # Frontend dependencies list
│   └── package-lock.json      # Dependency versions lockfile
│
├── .gitignore                 # Files excluded from GitHub
└── README.md                  # Project Documentation



## ⚡ How to Run Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/adaptive-placement-system.git](https://github.com/YOUR_USERNAME/adaptive-placement-system.git)
cd adaptive-placement-system
```
2. Setup the Backend (Python/FastAPI)
Open a terminal in the project root:

cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Server
uvicorn main:app --reload

3. Setup the Frontend (React)
Open a new terminal window (keep the backend running):

cd frontend

# Install Node dependencies
npm install

# Start the Dashboard
npm start

