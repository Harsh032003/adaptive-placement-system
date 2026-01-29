import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = "http://localhost:8000";

function App() {
  // Auth State
  const [user, setUser] = useState(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [loginError, setLoginError] = useState("");

  // Dashboard State
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [mastery, setMastery] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [attempts, setAttempts] = useState(0); // Track local attempts
  const [driftCount, setDriftCount] = useState(0);

  // Fetch question ONLY after login
  useEffect(() => {
    if (user) {
      fetchQuestion();
    }
  }, [user]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/login`, { username: usernameInput, password: passwordInput });
      setUser(usernameInput);
      setLoginError("");
    } catch (error) {
      setLoginError("Invalid credentials (try admin/password)");
    }
  };

  const fetchQuestion = async () => {
    try {
      const res = await axios.get(`${API_URL}/get-question`);
      setQuestion(res.data);
      setAnswer("");
      setFeedback(null);
    } catch (error) {
      console.error("Error fetching question", error);
    }
  };

  const handleSubmit = async () => {
    if (!question) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/submit`, {
        question_id: question.id,
        user_answer: answer,
        time_taken_seconds: 25
      });

      setFeedback(res.data);
      setMastery(res.data.skill_update);
      setAttempts(prev => prev + 1);
      if (res.data.drift_alert) setDriftCount(prev => prev + 1);
    } catch (error) {
      console.error("Error submitting", error);
    }
    setLoading(false);
  };

  // --- VIEW 1: LOGIN SCREEN ---
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center font-sans">
        <div className="bg-white p-8 rounded-lg shadow-md w-96">
          <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">Placement Prep AI</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                className="w-full border p-2 rounded mt-1"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                placeholder="admin"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                className="w-full border p-2 rounded mt-1"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="password"
              />
            </div>
            {loginError && <p className="text-red-500 text-sm">{loginError}</p>}
            <button
              type="submit"
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
            >
              Login
            </button>
          </form>
          <div className="mt-4 text-xs text-gray-400 text-center">
            Demo Credentials: admin / password
          </div>
        </div>
      </div>
    );
  }

  // --- VIEW 2: DASHBOARD ---
  return (
    <div className="min-h-screen bg-gray-100 p-10 font-sans">
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* LEFT COLUMN: The Quiz Interface */}
        <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-blue-600">Adaptive Practice</h2>
            <button onClick={() => setUser(null)} className="text-sm text-gray-500 underline">Logout</button>
          </div>

          {question ? (
            <div>
              <div className="mb-2 text-sm text-gray-500 uppercase tracking-wide">
                Topic: {question.topic} | Difficulty: <span className={`font-bold ${question.difficulty === 'hard' ? 'text-red-500' : 'text-green-500'}`}>{question.difficulty}</span>
              </div>
              <p className="text-lg mb-6">{question.text}</p>

              {!feedback ? (
                <div className="space-y-4">
                  <input
                    type="text"
                    className="w-full border p-2 rounded"
                    placeholder="Type your answer..."
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                  />
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
                  >
                    {loading ? "Analyzing..." : "Submit Answer"}
                  </button>
                </div>
              ) : (
                <div className={`p-4 rounded border ${feedback.correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                  <h3 className="font-bold">{feedback.correct ? "Excellent!" : "Not quite."}</h3>
                  <p className="mb-3">{feedback.explanation}</p>

                  {feedback.drift_alert && (
                    <div className="bg-yellow-100 text-yellow-800 p-2 text-sm rounded mb-3">
                      ⚠️ Skill Drift Detected: We have lowered the difficulty and provided a revision note.
                    </div>
                  )}

                  <button
                    onClick={() => setQuestion(feedback.next_question) || setFeedback(null) || setAnswer("")}
                    className="bg-gray-800 text-white px-4 py-2 rounded text-sm"
                  >
                    Next Question &rarr;
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p>Loading question...</p>
          )}
        </div>

        {/* RIGHT COLUMN: The Dashboard */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-bold mb-4">Live Mastery: {user}</h3>

          <div className="mb-6">
            <div className="flex justify-between text-sm mb-1">
              <span>Current Skill Level</span>
              <span>{Math.round(mastery * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${mastery * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="text-sm font-semibold text-gray-600 mb-2">Session Stats</h4>
            <ul className="text-sm space-y-2">
              <li className="flex justify-between">
                <span>Questions Attempted:</span>
                <span className="font-mono">{attempts}</span>
              </li>
              <li className="flex justify-between">
                <span>Drift Events:</span>
                <span className="font-mono">{driftCount}</span>
              </li>
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;