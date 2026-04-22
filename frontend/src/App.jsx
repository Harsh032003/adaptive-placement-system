import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

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

function AnalyticsPanel({ analytics }) {
  const [activeInsightTab, setActiveInsightTab] = useState("focus");
  const summary = analytics?.summary || {};
  const trend = analytics?.mastery_trend || [];
  const weakTopics = analytics?.weak_topics || [];
  const responseTimes = analytics?.response_time_by_topic || [];
  const driftFrequency = analytics?.drift_frequency_by_topic || [];
  const primaryWeakTopic = weakTopics[0];

  if (!analytics || (summary.total_attempts || 0) === 0) {
    return <p className="hint">Complete a few questions to unlock deeper learning insights.</p>;
  }

  return (
    <div className="analytics-panel">
      <div className="insight-grid">
        <div className="insight-tile">
          <span>Accuracy</span>
          <strong>{summary.accuracy_percent}%</strong>
        </div>
        <div className="insight-tile">
          <span>Avg Time</span>
          <strong>{summary.avg_time_seconds}s</strong>
        </div>
        <div className="insight-tile">
          <span>Drift Events</span>
          <strong>{summary.drift_events}</strong>
        </div>
      </div>

      {primaryWeakTopic && (
        <div className="priority-insight">
          <span>Priority Focus</span>
          <strong>{primaryWeakTopic.topic}</strong>
          <p>{primaryWeakTopic.recommendation}</p>
        </div>
      )}

      <div className="insight-tabs">
        <button
          className={activeInsightTab === "focus" ? "active" : ""}
          onClick={() => setActiveInsightTab("focus")}
        >
          Focus
        </button>
        <button
          className={activeInsightTab === "speed" ? "active" : ""}
          onClick={() => setActiveInsightTab("speed")}
        >
          Speed
        </button>
        <button
          className={activeInsightTab === "drift" ? "active" : ""}
          onClick={() => setActiveInsightTab("drift")}
        >
          Drift
        </button>
      </div>

      {activeInsightTab === "focus" && (
        <div className="insight-block">
          <div className="insight-heading">
            <strong>Weak Topics</strong>
            <span>Lowest mastery first</span>
          </div>
          <div className="mini-list">
            {weakTopics.map((topic) => (
              <div key={topic.topic} className="mini-list-item">
                <div>
                  <strong>{topic.topic}</strong>
                  <span>{topic.recommendation}</span>
                </div>
                <em>{topic.mastery_percent}%</em>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeInsightTab === "speed" && (
        <div className="insight-block">
          <div className="insight-heading">
            <strong>Response Time</strong>
            <span>Slowest topics first</span>
          </div>
          <div className="mini-list">
            {responseTimes.slice(0, 4).map((topic) => (
              <div key={topic.topic} className="mini-list-item compact">
                <span>{topic.topic}</span>
                <em>{topic.avg_time_seconds}s</em>
              </div>
            ))}
          </div>
          <div className="insight-heading" style={{ marginTop: 8 }}>
            <strong>Mastery Trend</strong>
            <span>Last {trend.length} attempts</span>
          </div>
          <div className="trend-bars">
            {trend.map((point) => (
              <div
                key={`${point.attempt}-${point.created_at}`}
                className="trend-bar"
                title={`${point.topic}: ${point.mastery_percent}%`}
                style={{ height: `${Math.max(8, point.mastery_percent)}%` }}
              />
            ))}
          </div>
        </div>
      )}

      {activeInsightTab === "drift" && (
        <div className="insight-block">
          <div className="insight-heading">
            <strong>Drift Frequency</strong>
            <span>Higher means more struggle</span>
          </div>
          <div className="mini-list">
            {driftFrequency.slice(0, 4).map((topic) => (
              <div key={topic.topic} className="mini-list-item compact">
                <span>{topic.topic}</span>
                <em>{topic.drift_events} events</em>
              </div>
            ))}
          </div>
        </div>
      )}
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
  const [questionStartedAt, setQuestionStartedAt] = useState(null);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [mastery, setMastery] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [driftCount, setDriftCount] = useState(0);
  const [topicStats, setTopicStats] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [availableTopics, setAvailableTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState("All Topics");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [questionError, setQuestionError] = useState("");

  const [questionForm, setQuestionForm] = useState({
    topic: "",
    difficulty: "easy",
    text: "",
    options: ["", "", "", ""],
    correct_option: "A",
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
  const [adminSuccess, setAdminSuccess] = useState("");
  const [editingQuestionId, setEditingQuestionId] = useState(null);
  const [editingNoteId, setEditingNoteId] = useState(null);

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

  const setAuth = (payload) => {
    setToken(payload.access_token);
    setUser(payload.user);
    localStorage.setItem("token", payload.access_token);
    localStorage.setItem("user", JSON.stringify(payload.user));
    setAuthError("");
  };

  const setActiveQuestion = (nextQuestion) => {
    setQuestion(nextQuestion);
    setAnswer("");
    setFeedback(null);
    setSubmitError("");
    setQuestionError("");
    setQuestionStartedAt(nextQuestion ? Date.now() : null);
  };

  const currentTopicFilter = selectedTopic === "All Topics" ? null : selectedTopic;

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
    setAnalytics(null);
    setAvailableTopics([]);
    setSelectedTopic("All Topics");
    setQuestionError("");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  };

  const fetchQuestion = useCallback(async (topicOverride = currentTopicFilter) => {
    try {
      setQuestionError("");
      const res = await axios.get(`${API_URL}/get-question`, {
        params: topicOverride ? { topic: topicOverride } : {},
      });
      setActiveQuestion(res.data);
    } catch (error) {
      console.error("Error fetching question", error);
      setQuestion(null);
      setAnswer("");
      setFeedback(null);
      setQuestionStartedAt(null);
      setQuestionError(
        topicOverride
          ? `No questions available for ${topicOverride} right now.`
          : "No questions available right now."
      );
    }
  }, [currentTopicFilter]);

  const loadTopics = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/topics`);
      setAvailableTopics(res.data.topics || []);
    } catch (error) {
      console.error("Error loading topics", error);
    }
  }, []);

  const handleSubmit = async () => {
    if (!question) return;
    if (!answer) {
      setSubmitError("Select one option before submitting.");
      return;
    }
    setLoading(true);
    setSubmitError("");
    const elapsedSeconds = questionStartedAt
      ? Math.max(1, Math.round((Date.now() - questionStartedAt) / 1000))
      : 1;
    try {
      const res = await axios.post(`${API_URL}/submit`, {
        question_id: question.id,
        user_answer: answer,
        time_taken_seconds: elapsedSeconds,
        selected_topic: currentTopicFilter,
      });

      setFeedback(res.data);
      setMastery(res.data.skill_update);
      setAttempts((prev) => prev + 1);
      if (res.data.drift_alert) setDriftCount((prev) => prev + 1);
      loadTopicMastery();
      loadUserAnalytics();
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

  const resetQuestionForm = () => {
    setEditingQuestionId(null);
    setQuestionForm({
      topic: "",
      difficulty: "easy",
      text: "",
      options: ["", "", "", ""],
      correct_option: "A",
    });
  };

  const handleSaveQuestion = async (e) => {
    e.preventDefault();
    setAdminError("");
    setAdminSuccess("");
    try {
      if (editingQuestionId) {
        await axios.put(`${API_URL}/admin/questions/${editingQuestionId}`, questionForm);
        setAdminSuccess("Question updated successfully.");
      } else {
        await axios.post(`${API_URL}/admin/questions`, questionForm);
        setAdminSuccess("Question created successfully.");
      }
      resetQuestionForm();
      loadTopics();
      loadAdminData();
    } catch (error) {
      setAdminError(editingQuestionId ? "Failed to update question" : "Failed to create question");
    }
  };

  const handleEditQuestion = (questionToEdit) => {
    setEditingQuestionId(questionToEdit.id);
    setAdminError("");
    setAdminSuccess("");
    setQuestionForm({
      topic: questionToEdit.topic || "",
      difficulty: questionToEdit.difficulty || "easy",
      text: questionToEdit.text || "",
      options: questionToEdit.options || ["", "", "", ""],
      correct_option: questionToEdit.correct_option || "A",
    });
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Delete this question? Related attempt logs may also be removed.")) return;
    setAdminError("");
    setAdminSuccess("");
    try {
      await axios.delete(`${API_URL}/admin/questions/${questionId}`);
      if (editingQuestionId === questionId) resetQuestionForm();
      setAdminSuccess("Question deleted successfully.");
      loadTopics();
      loadAdminData();
      loadTopicMastery();
      loadUserAnalytics();
    } catch (error) {
      setAdminError("Failed to delete question");
    }
  };

  const handleQuestionOptionChange = (index, value) => {
    setQuestionForm((current) => {
      const nextOptions = [...current.options];
      nextOptions[index] = value;
      return { ...current, options: nextOptions };
    });
  };

  const resetNoteForm = () => {
    setEditingNoteId(null);
    setNoteForm({ title: "", topic: "", content: "", file: null });
  };

  const handleSaveNote = async (e) => {
    e.preventDefault();
    setAdminError("");
    setAdminSuccess("");
    try {
      const formData = new FormData();
      formData.append("title", noteForm.title);
      if (noteForm.topic) formData.append("topic", noteForm.topic);
      if (noteForm.content) formData.append("content", noteForm.content);
      if (noteForm.file) formData.append("file", noteForm.file);

      const url = editingNoteId
        ? `${API_URL}/admin/theory-notes/${editingNoteId}`
        : `${API_URL}/admin/theory-notes`;
      const wasEditing = Boolean(editingNoteId);
      await (wasEditing ? axios.put : axios.post)(url, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      resetNoteForm();
      setAdminSuccess(
        wasEditing
          ? "Note updated. Re-ingestion was attempted automatically."
          : "Note uploaded. Ingestion was attempted automatically."
      );
      loadAdminData();
    } catch (error) {
      setAdminError(editingNoteId ? "Failed to update note" : "Failed to upload note");
    }
  };

  const handleEditNote = (noteToEdit) => {
    setEditingNoteId(noteToEdit.id);
    setAdminError("");
    setAdminSuccess("");
    setNoteForm({
      title: noteToEdit.title || "",
      topic: noteToEdit.topic || "",
      content: noteToEdit.content || "",
      file: null,
    });
  };

  const handleDeleteNote = async (noteId) => {
    if (!window.confirm("Delete this theory note and its embeddings?")) return;
    setAdminError("");
    setAdminSuccess("");
    try {
      await axios.delete(`${API_URL}/admin/theory-notes/${noteId}`);
      if (editingNoteId === noteId) resetNoteForm();
      setAdminSuccess("Theory note deleted successfully.");
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to delete note");
    }
  };

  const handleToggleAdmin = async (userId, isAdmin) => {
    setAdminError("");
    setAdminSuccess("");
    try {
      await axios.patch(`${API_URL}/admin/users/${userId}`, { is_admin: !isAdmin });
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to update user permissions");
    }
  };

  const handleIngestNote = async (noteId) => {
    setAdminError("");
    setAdminSuccess("");
    try {
      await axios.post(`${API_URL}/admin/theory-notes/${noteId}/ingest`);
      setAdminSuccess("Note ingested successfully.");
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to ingest note.");
    }
  };

  const handleIngestAllNotes = async () => {
    setAdminError("");
    setAdminSuccess("");
    try {
      const res = await axios.post(`${API_URL}/admin/theory-notes/ingest-all`);
      setAdminSuccess(res.data.message || "All notes ingested successfully.");
      loadAdminData();
    } catch (error) {
      setAdminError("Failed to ingest all notes.");
    }
  };

  const loadTopicMastery = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/stats/topic-mastery`);
      setTopicStats(res.data.topics || []);
    } catch (error) {
      console.error("Error loading topic mastery", error);
    }
  }, []);

  const loadUserAnalytics = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/analytics/user`);
      setAnalytics(res.data);
    } catch (error) {
      console.error("Error loading user analytics", error);
    }
  }, []);

  useEffect(() => {
    if (user) {
      loadTopics();
      fetchQuestion(currentTopicFilter);
      loadTopicMastery();
      loadUserAnalytics();
    }
  }, [user, currentTopicFilter, fetchQuestion, loadTopics, loadTopicMastery, loadUserAnalytics]);

  const handleTopicChange = (topic) => {
    setSelectedTopic(topic);
    setQuestion(null);
    setFeedback(null);
    setAnswer("");
    setQuestionStartedAt(null);
    setQuestionError("");
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
      loadUserAnalytics();
    }
    if (user && view === "quiz") {
      loadTopicMastery();
      loadUserAnalytics();
    }
  }, [user, view, loadTopicMastery, loadUserAnalytics]);

  if (!user) {
    return (
      <div className="auth-shell">
        <div className="auth-panel">
          <div className="card auth-card auth-card-compact">
            <div className="auth-header auth-header-centered">
              <span className="auth-kicker">Adaptive Interview Preparation</span>
              {/* <h2 className="auth-title">Placement Prep AI</h2> */}
              <p className="hint auth-subtitle">Build your core CS foundations with adaptive practice.</p>
            </div>
            <div className="tabs auth-tabs">
              <button className={`tab ${authMode === 'login' ? 'active' : ''}`} onClick={() => setAuthMode("login")}>Login</button>
              <button className={`tab ${authMode === 'signup' ? 'active' : ''}`} onClick={() => setAuthMode("signup")}>Sign Up</button>
            </div>
            <form className="auth-form" onSubmit={authMode === "login" ? handleLogin : handleSignup}>
              <div className="field auth-field">
                <label>Username</label>
                <input value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)} placeholder="yourname" />
              </div>
              <div className="field auth-field">
                <label>Password</label>
                <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} placeholder="••••••••" />
              </div>
              {authMode === "signup" && (
                <div className="field auth-field">
                  <label>Admin Code (optional)</label>
                  <input value={adminCodeInput} onChange={(e) => setAdminCodeInput(e.target.value)} placeholder="ADMIN_SIGNUP_CODE" />
                </div>
              )}
              {authError && <p className="error auth-error">{authError}</p>}
              <button type="submit" className="btn btn-primary auth-submit">
                {authMode === "login" ? "Login" : "Create Account"}
              </button>
            </form>
          </div>
          <div className="auth-caption">
            <span>Topic-aware practice</span>
            <span>AI-based drift detection</span>
            <span>Note-grounded explanations</span>
          </div>
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
              <div className="list-header">
                <h3 className="section-title">{editingQuestionId ? "Edit Question" : "Add Question"}</h3>
                {editingQuestionId && (
                  <button className="btn" type="button" onClick={resetQuestionForm}>Cancel</button>
                )}
              </div>
              <form onSubmit={handleSaveQuestion}>
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
                  <label>Option A</label>
                  <input value={questionForm.options[0]} onChange={(e) => handleQuestionOptionChange(0, e.target.value)} />
                </div>
                <div className="field">
                  <label>Option B</label>
                  <input value={questionForm.options[1]} onChange={(e) => handleQuestionOptionChange(1, e.target.value)} />
                </div>
                <div className="field">
                  <label>Option C</label>
                  <input value={questionForm.options[2]} onChange={(e) => handleQuestionOptionChange(2, e.target.value)} />
                </div>
                <div className="field">
                  <label>Option D</label>
                  <input value={questionForm.options[3]} onChange={(e) => handleQuestionOptionChange(3, e.target.value)} />
                </div>
                <div className="field">
                  <label>Correct Option</label>
                  <select
                    value={questionForm.correct_option}
                    onChange={(e) => setQuestionForm({ ...questionForm, correct_option: e.target.value })}
                  >
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                  </select>
                </div>
                <button className="btn btn-primary" type="submit">
                  {editingQuestionId ? "Update Question" : "Save Question"}
                </button>
              </form>
            </div>

            <div className="card card-pad">
              <div className="list-header">
                <h3 className="section-title">{editingNoteId ? "Edit Theory Note" : "Upload Theory Note"}</h3>
                {editingNoteId && (
                  <button className="btn" type="button" onClick={resetNoteForm}>Cancel</button>
                )}
              </div>
              <form onSubmit={handleSaveNote}>
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
                  <label>{editingNoteId ? "Replace PDF (optional)" : "Upload PDF"}</label>
                  <input type="file" onChange={(e) => setNoteForm({ ...noteForm, file: e.target.files[0] })} />
                </div>
                <button className="btn btn-primary" type="submit">
                  {editingNoteId ? "Update Note" : "Upload Note"}
                </button>
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
                          <div className="action-row">
                            <button className="btn" onClick={() => handleEditQuestion(q)}>Edit</button>
                            <button className="btn btn-danger" onClick={() => handleDeleteQuestion(q.id)}>Delete</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <div className="list-header">
                      <h4 className="section-title">Theory Notes</h4>
                      <button className="btn" onClick={handleIngestAllNotes}>Ingest All</button>
                    </div>
                    <div className="list">
                      {adminNotes.map((n) => (
                        <div key={n.id} className="list-item">
                          <strong>{n.title}</strong>
                          {n.topic && <div className="hint">Topic: {n.topic}</div>}
                          <div className="hint">
                            Status: {n.ingestion_status} • Chunks: {n.embedding_chunks || 0}
                          </div>
                          {n.ingestion_error && <div className="error">{n.ingestion_error}</div>}
                          {n.content && <div className="hint">{n.content}</div>}
                          {n.file_url && (
                            <div className="hint">
                              <a href={`${API_URL}${n.file_url}`} target="_blank" rel="noreferrer">Download</a>
                            </div>
                          )}
                          <div className="action-row">
                            <button className="btn" onClick={() => handleIngestNote(n.id)}>Ingest Now</button>
                            <button className="btn" onClick={() => handleEditNote(n)}>Edit</button>
                            <button className="btn btn-danger" onClick={() => handleDeleteNote(n.id)}>Delete</button>
                          </div>
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
              {adminSuccess && <p className="hint" style={{ marginTop: 8 }}>{adminSuccess}</p>}
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
                      <p style={{ marginTop: 6 }}>Your Answer: {item.user_answer_text || item.user_answer}</p>
                      <p style={{ marginTop: 6, color: item.correct ? '#0f766e' : '#b91c1c' }}>
                        {item.correct ? "Correct" : "Incorrect"}
                      </p>
                      {!item.correct && item.correct_answer_text && (
                        <p style={{ marginTop: 6 }}>Correct Answer: {item.correct_answer_text}</p>
                      )}
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
              <div style={{ borderTop: '1px solid var(--line)', marginTop: 18, paddingTop: 18 }}>
                <h3 className="section-title">Learning Insights</h3>
                <AnalyticsPanel analytics={analytics} />
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-3">
            <div className="card card-pad">
              <div className="hero-card">
                <h3>Adaptive Practice</h3>
                <p>Answer questions. We adjust difficulty and explanations in real time.</p>
              </div>
              <div className="topic-tabs">
                <button
                  className={`topic-tab ${selectedTopic === "All Topics" ? 'active' : ''}`}
                  onClick={() => handleTopicChange("All Topics")}
                >
                  All Topics
                </button>
                {availableTopics.map((topic) => (
                  <button
                    key={topic}
                    className={`topic-tab ${selectedTopic === topic ? 'active' : ''}`}
                    onClick={() => handleTopicChange(topic)}
                  >
                    {topic}
                  </button>
                ))}
              </div>
              {question ? (
                <div className="fade-in">
                  <div className={`badge ${question.difficulty}`}>
                    {question.topic} • {question.difficulty}
                  </div>
                  <div className="question-meta">
                    <span>Question #{attempts + 1}</span>
                    <span>{currentTopicFilter ? `${currentTopicFilter} focus mode` : "Adaptive practice mode"}</span>
                  </div>
                  <div className="divider"></div>
                  <p style={{ fontSize: 18 }}>{question.text}</p>

                  {!feedback ? (
                    <div style={{ marginTop: 16 }}>
                      <div className="mcq-group">
                        {(question.options || []).map((option, index) => {
                          const optionKey = String.fromCharCode(65 + index);
                          const checked = answer === optionKey;
                          return (
                            <label key={optionKey} className={`mcq-option ${checked ? 'selected' : ''}`}>
                              <input
                                type="radio"
                                name={`question-${question.id}`}
                                value={optionKey}
                                checked={checked}
                                onChange={(e) => setAnswer(e.target.value)}
                              />
                              <span className="mcq-option-key">{optionKey}</span>
                              <span className="mcq-option-text">{option}</span>
                            </label>
                          );
                        })}
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
                      <button className="btn" style={{ marginTop: 12 }} onClick={() => setActiveQuestion(feedback.next_question)}>Next Question</button>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {questionError ? (
                    <p className="hint">{questionError}</p>
                  ) : (
                    <>
                      <div className="skeleton" style={{ height: 18, width: '70%', marginBottom: 12 }}></div>
                      <div className="skeleton" style={{ height: 12, width: '90%', marginBottom: 8 }}></div>
                      <div className="skeleton" style={{ height: 12, width: '80%' }}></div>
                    </>
                  )}
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
              <div style={{ borderTop: '1px solid var(--line)', marginTop: 18, paddingTop: 18 }}>
                <h4 className="section-title">Learning Insights</h4>
                <AnalyticsPanel analytics={analytics} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
