import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = "http://localhost:8000";

function MasteryBars({ data }) {
  const topics = data || [];
  return (
    <div className="bars">
      {topics.map((topic) => (
        <div key={topic.topic} className="bars-row">
          <div className="bars-label">
            <span>{topic.topic}</span>
            <strong>{topic.percent}%</strong>
          </div>
          <div className="bars-track">
            <div className="bars-fill" style={{ width: `${topic.percent}%` }}></div>
          </div>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [adminCodeInput, setAdminCodeInput] = useState("");
  const [authError, setAuthError] = useState("");
  const [view, setView] = useState("quiz");

  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [mastery, setMastery] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [driftCount, setDriftCount] = useState(0);
  const [topicStats, setTopicStats] = useState([]);
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");

  const [questionForm, setQuestionForm] = useState({
    topic: "",
    difficulty: "easy",
    text: "",
    correct: "",
  });
  const [noteForm, setNoteForm] = useState({
    title: "",
    topic: "",
    content: "",
    file: null,
  });
  const [adminQuestions, setAdminQuestions] = useState([]);
  const [adminNotes, setAdminNotes] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminError, setAdminError] = useState("");

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common.Authorization;
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      fetchQuestion();
      loadTopicMastery();
    }
  }, [user]);

  const setAuth = (payload) => {
    setToken(payload.access_token);
    setUser(payload.user);
    localStorage.setItem("token", payload.access_token);
    localStorage.setItem("user", JSON.stringify(payload.user));
    setAuthError("");
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_URL}/login`, {
        username: usernameInput,
        password: passwordInput,
      });
      setAuth(res.data);
    } catch (error) {
      setAuthError("Invalid credentials");
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_URL}/signup`, {
        username: usernameInput,
        password: passwordInput,
        admin_code: adminCodeInput || undefined,
      });
      setAuth(res.data);
    } catch (error) {
      setAuthError("Could not create account");
    }
  };

  const handleLogout = () => {
    setUser(null);
    setToken("");
    setView("quiz");
    setQuestion(null);
    setFeedback(null);
    setAnswer("");
    setAttempts(0);
    setDriftCount(0);
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const fetchQuestion = async () => {
    try {
      const res = await axios.get(`${API_URL}/get-question`);
      setQuestion(res.data);
      setAnswer("");
      setFeedback(null);
      setSubmitError("");
    } catch (error) {
      console.error("Error fetching question", error);
    }
  };

  const handleSubmit = async () => {
    if (!question) return;
    setLoading(true);
    setSubmitError("");
    try {
      const res = await axios.post(`${API_URL}/submit`, {
        question_id: question.id,
        user_answer: answer,
        time_taken_seconds: 25,
      });

      setFeedback(res.data);
      setMastery(res.data.skill_update);
      setAttempts((prev) => prev + 1);
      if (res.data.drift_alert) setDriftCount((prev) => prev + 1);
      loadTopicMastery();
    } catch (error) {
      console.error("Error submitting", error);
      setSubmitError("We could not submit your answer. Please try again.");
    }
    setLoading(false);
  };

  const loadAdminData = async () => {
    setAdminLoading(true);
    setAdminError("");
    try {
      const [questionsRes, notesRes, usersRes] = await Promise.all([
        axios.get(`${API_URL}/admin/questions`),
        axios.get(`${API_URL}/admin/theory-notes`),
        axios.get(`${API_URL}/admin/users`),
      ]);
      setAdminQuestions(questionsRes.data);
      setAdminNotes(notesRes.data);
      setAdminUsers(usersRes.data);
    } catch (error) {
      setAdminError("Failed to load admin data");
    }
    setAdminLoading(false);
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    setAdminError("");
    try {
      await axios.post(`${API_URL}/admin/questions`, questionForm);
      setQuestionForm({ topic: "", difficulty: "easy", text: "", correct: "" });
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to create question");
    }
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();
    setAdminError("");
    try {
      const formData = new FormData();
      formData.append("title", noteForm.title);
      if (noteForm.topic) formData.append("topic", noteForm.topic);
      if (noteForm.content) formData.append("content", noteForm.content);
      if (noteForm.file) formData.append("file", noteForm.file);

      await axios.post(`${API_URL}/admin/theory-notes`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setNoteForm({ title: "", topic: "", content: "", file: null });
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to upload note");
    }
  };

  const handleToggleAdmin = async (userId, isAdmin) => {
    setAdminError("");
    try {
      await axios.patch(`${API_URL}/admin/users/${userId}`, { is_admin: !isAdmin });
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to update user permissions");
    }
  };

  const loadTopicMastery = async () => {
    try {
      const res = await axios.get(`${API_URL}/stats/topic-mastery`);
      setTopicStats(res.data.topics || []);
    } catch (error) {
      console.error("Error loading topic mastery", error);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const res = await axios.get(`${API_URL}/history`);
      setHistoryItems(res.data.items || []);
    } catch (error) {
      setHistoryError("Failed to load history.");
    }
    setHistoryLoading(false);
  };

  useEffect(() => {
    if (user?.is_admin && view === "admin") {
      loadAdminData();
    }
    if (user && view === "history") {
      loadHistory();
    }
    if (user && view === "quiz") {
      loadTopicMastery();
    }
  }, [user, view]);

  if (!user) {
    return (
      <div className="auth-shell">
        <div className="card auth-card">
          <div className="auth-header">
            <h2 className="auth-title">Placement Prep AI</h2>
            <p className="hint">Build your core CS foundations with adaptive practice.</p>
          </div>
          <div className="tabs">
            <button className={`tab ${authMode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode("login")}>Login</button>
            <button className={`tab ${authMode === 'signup' ? 'active' : ''}`} onClick={() => setAuthMode("signup")}>Sign Up</button>
          </div>
          <form onSubmit={authMode === "login" ? handleLogin : handleSignup}>
            <div className="field">
              <label>Username</label>
              <input value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)} placeholder="yourname" />
            </div>
            <div className="field">
              <label>Password</label>
              <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} placeholder="••••••••" />
            </div>
            {authMode === "signup" && (
              <div className="field">
                <label>Admin Code (optional)</label>
                <input value={adminCodeInput} onChange={(e) => setAdminCodeInput(e.target.value)} placeholder="ADMIN_SIGNUP_CODE" />
              </div>
            )}
            {authError && <p className="error">{authError}</p>}
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: 8 }}>
              {authMode === "login" ? "Login" : "Create Account"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div className="container">
        <div className="topbar topbar-card">
          <div className="brand">
            <h1>Placement Prep AI</h1>
            <p>Personalized practice and diagnostic feedback for {user.username}</p>
          </div>
          <div className="nav-actions">
            <div className="tabs segmented">
              <button className={`tab ${view === "quiz" ? "active" : ""}`} onClick={() => setView("quiz")}>Practice</button>
              <button className={`tab ${view === "history" ? "active" : ""}`} onClick={() => setView("history")}>History</button>
              {user.is_admin && (
                <button className={`tab ${view === "admin" ? "active" : ""}`} onClick={() => setView("admin")}>Admin</button>
              )}
            </div>
            <button className="btn btn-ghost logout" onClick={handleLogout}>Logout</button>
          </div>
        </div>

        {view === "admin" && user.is_admin ? (
          <div className="grid grid-2">
            <div className="card card-pad">
              <h3 className="section-title">Add Question</h3>
              <form onSubmit={handleCreateQuestion}>
                <div className="field">
                  <label>Topic</label>
                  <input value={questionForm.topic} onChange={(e) => setQuestionForm({ ...questionForm, topic: e.target.value })} />
                </div>
                <div className="field">
                  <label>Difficulty</label>
                  <select value={questionForm.difficulty} onChange={(e) => setQuestionForm({ ...questionForm, difficulty: e.target.value })}>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div className="field">
                  <label>Question</label>
                  <textarea value={questionForm.text} onChange={(e) => setQuestionForm({ ...questionForm, text: e.target.value })} />
                </div>
                <div className="field">
                  <label>Correct Answer</label>
                  <textarea value={questionForm.correct} onChange={(e) => setQuestionForm({ ...questionForm, correct: e.target.value })} />
                </div>
                <button className="btn btn-primary" type="submit">Save Question</button>
              </form>
            </div>

            <div className="card card-pad">
              <h3 className="section-title">Upload Theory Note</h3>
              <form onSubmit={handleCreateNote}>
                <div className="field">
                  <label>Title</label>
                  <input value={noteForm.title} onChange={(e) => setNoteForm({ ...noteForm, title: e.target.value })} />
                </div>
                <div className="field">
                  <label>Topic (optional)</label>
                  <input value={noteForm.topic} onChange={(e) => setNoteForm({ ...noteForm, topic: e.target.value })} />
                </div>
                <div className="field">
                  <label>Text Notes (optional)</label>
                  <textarea value={noteForm.content} onChange={(e) => setNoteForm({ ...noteForm, content: e.target.value })} />
                </div>
                <div className="field">
                  <label>Upload PDF</label>
                  <input type="file" onChange={(e) => setNoteForm({ ...noteForm, file: e.target.files[0] })} />
                </div>
                <button className="btn btn-primary" type="submit">Upload Note</button>
              </form>
            </div>

            <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
              <div className="topbar" style={{ marginBottom: 16 }}>
                <h3 className="section-title">Content Library</h3>
                <button className="btn" onClick={loadAdminData}>Refresh</button>
              </div>
              {adminLoading ? (
                <p className="hint">Loading...</p>
              ) : (
                <div className="grid grid-2">
                  <div>
                    <h4 className="section-title">Questions</h4>
                    <div className="list">
                      {adminQuestions.map((q) => (
                        <div key={q.id} className="list-item">
                          <strong>{q.topic} ({q.difficulty})</strong>
                          <div className="hint">{q.text}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="section-title">Theory Notes</h4>
                    <div className="list">
                      {adminNotes.map((n) => (
                        <div key={n.id} className="list-item">
                          <strong>{n.title}</strong>
                          {n.topic && <div className="hint">Topic: {n.topic}</div>}
                          {n.content && <div className="hint">{n.content}</div>}
                          {n.file_url && (
                            <div className="hint">
                              <a href={`${API_URL}${n.file_url}`} target="_blank" rel="noreferrer">Download</a>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <h4 className="section-title">Users</h4>
                    <div className="list">
                      {adminUsers.map((u) => (
                        <div key={u.id} className="list-item" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <div>
                            <strong>{u.username}</strong>
                            <div className="hint">{u.is_admin ? "Admin" : "User"}</div>
                          </div>
                          <button className="btn" onClick={() => handleToggleAdmin(u.id, u.is_admin)}>
                            {u.is_admin ? "Revoke Admin" : "Make Admin"}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              {adminError && <p className="error">{adminError}</p>}
            </div>
          </div>
        ) : view === "history" ? (
          <div className="grid grid-2">
            <div className="card card-pad">
              <div className="topbar" style={{ marginBottom: 16 }}>
                <h3 className="section-title">Previous Tests</h3>
                <button className="btn" onClick={loadHistory}>Refresh</button>
              </div>
              {historyLoading ? (
                <p className="hint">Loading history...</p>
              ) : historyError ? (
                <p className="error">{historyError}</p>
              ) : historyItems.length === 0 ? (
                <p className="hint">No attempts yet.</p>
              ) : (
                <div className="list">
                  {historyItems.map((item) => (
                    <div key={item.id} className="list-item">
                      <small>{item.topic || "Unknown"} • {item.difficulty || "N/A"} • {new Date(item.created_at).toLocaleString()}</small>
                      <p style={{ marginTop: 8 }}><strong>{item.question}</strong></p>
                      <p style={{ marginTop: 6 }}>Your Answer: {item.user_answer}</p>
                      <p style={{ marginTop: 6, color: item.correct ? '#0f766e' : '#b91c1c' }}>
                        {item.correct ? "Correct" : "Incorrect"}
                      </p>
                      {item.explanation && (
                        <p style={{ marginTop: 8 }}><strong>Explanation:</strong> {item.explanation}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="card card-pad">
              <h3 className="section-title">Topic Mastery</h3>
              {topicStats.length === 0 ? (
                <p className="hint">No topic data yet.</p>
              ) : (
                <MasteryBars data={topicStats} />
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-3">
            <div className="card card-pad">
              <div className="hero-card">
                <h3>Adaptive Practice</h3>
                <p>Answer questions. We adjust difficulty and explanations in real time.</p>
              </div>
              {question ? (
                <div className="fade-in">
                  <div className={`badge ${question.difficulty}`}>
                    {question.topic} • {question.difficulty}
                  </div>
                  <div className="question-meta">
                    <span>Question #{attempts + 1}</span>
                    <span>Adaptive practice mode</span>
                  </div>
                  <div className="divider"></div>
                  <p style={{ fontSize: 18 }}>{question.text}</p>

                  {!feedback ? (
                    <div style={{ marginTop: 16 }}>
                      <div className="field">
                        <label>Your Answer</label>
                        <input value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Type your answer" />
                      </div>
                      <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
                        {loading ? (<span style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}><span className="spinner" /> Analyzing...</span>) : "Submit Answer"}
                      </button>
                      {submitError && <p className="error">{submitError}</p>}
                    </div>
                  ) : (
                    <div className={`feedback ${feedback.correct ? 'good' : 'bad'}`}>
                      <strong>{feedback.correct ? "Excellent." : "Needs Review."}</strong>
                      {loading ? (
                        <div>
                          <div className="skeleton" style={{ height: 10, width: '90%' }}></div>
                          <div className="skeleton" style={{ height: 10, width: '80%' }}></div>
                        </div>
                      ) : (
                        <p style={{ marginTop: 6 }}>{feedback.explanation}</p>
                      )}
                      {feedback.drift_alert && (
                        <div className="alert">Skill drift detected. We lowered the difficulty and provided revision notes.</div>
                      )}
                      <button className="btn" style={{ marginTop: 12 }} onClick={() => setQuestion(feedback.next_question) || setFeedback(null) || setAnswer("")}>Next Question</button>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="skeleton" style={{ height: 18, width: '70%', marginBottom: 12 }}></div>
                  <div className="skeleton" style={{ height: 12, width: '90%', marginBottom: 8 }}></div>
                  <div className="skeleton" style={{ height: 12, width: '80%' }}></div>
                </div>
              )}
            </div>

            <div className="card card-pad">
              <h3 className="section-title">Topic Mastery</h3>
              {topicStats.length === 0 ? (
                <p className="hint">No topic data yet.</p>
              ) : (
                <MasteryBars data={topicStats} />
              )}
              <div style={{ borderTop: '1px solid var(--line)', marginTop: 18, paddingTop: 18 }}>
                <h4 className="section-title">Session Stats</h4>
                <div className="stat-list">
                  <div className="stat-row"><span>Questions Attempted</span><span>{attempts}</span></div>
                  <div className="stat-row"><span>Drift Events</span><span>{driftCount}</span></div>
                  <div className="stat-row"><span>Current Skill</span><span>{Math.round(mastery * 100)}%</span></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
