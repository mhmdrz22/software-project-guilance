import React, { useEffect, useState } from "react";
import {
  fetchTasks,
  createTask,
  updateTask,
  deleteTask,
  loginUser,
  registerUser,
  fetchCurrentUser,
  clearAuthTokens,
} from "./api";

const STATUS_LABELS = {
  TODO: "To Do",
  DOING: "Doing",
  DONE: "Done",
};

const PRIORITY_LABELS = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [taskFormError, setTaskFormError] = useState("");
  const [editingTask, setEditingTask] = useState(null);
  const [draggingId, setDraggingId] = useState(null);
  const [dragOverStatus, setDragOverStatus] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("login");
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");
  const [authFieldErrors, setAuthFieldErrors] = useState({});

  useEffect(() => {
    bootstrap();
  }, []);

  async function bootstrap() {
    try {
      const me = await fetchCurrentUser();
      setUser(me);
      await loadTasks();
    } catch {
      clearAuthTokens();
    } finally {
      setAuthLoading(false);
      setLoading(false);
    }
  }

  async function loadTasks() {
    try {
      setLoading(true);
      setError("");
      const data = await fetchTasks();
      setTasks(data);
    } catch (err) {
      setError(err.message || "Unable to load tasks.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAuthSubmit(formData) {
    try {
      setAuthLoading(true);
      setAuthError("");
      setAuthFieldErrors({});
      if (authMode === "register") {
        await registerUser({
          email: formData.email,
          username: formData.username || formData.email,
          password: formData.password,
        });
      }
      await loginUser({ email: formData.email, password: formData.password });
      const me = await fetchCurrentUser();
      setUser(me);
      await loadTasks();
    } catch (err) {
      const data = err.data || {};
      const fieldErrs = {};
      ["email", "username", "password"].forEach((field) => {
        if (data[field]) {
          fieldErrs[field] = Array.isArray(data[field])
            ? data[field].join(" ")
            : String(data[field]);
        }
      });
      if (data.detail) {
        fieldErrs.general = Array.isArray(data.detail)
          ? data.detail.join(" ")
          : String(data.detail);
      }
      setAuthFieldErrors(fieldErrs);
      setAuthError(err.message || "Authentication failed.");
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    clearAuthTokens();
    setUser(null);
    setTasks([]);
  }

  async function handleCreateTask(formData) {
    try {
      setCreating(true);
      setTaskFormError("");
      const newTask = await createTask(formData);
      setTasks((prev) => [newTask, ...prev]);
    } catch (err) {
      setTaskFormError(err.message || "Unable to create task.");
    } finally {
      setCreating(false);
    }
  }

  async function handleStatusChange(task, newStatus) {
    if (task.status === newStatus) return;
    const previousTasks = [...tasks];
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t)),
    );
    try {
      await updateTask(task.id, { status: newStatus });
    } catch (err) {
      setError(err.message || "Unable to update task status.");
      setTasks(previousTasks);
    }
  }

  async function handleDelete(taskId) {
    const previousTasks = [...tasks];
    setTasks((prev) => prev.filter((t) => t.id !== taskId));
    try {
      await deleteTask(taskId);
    } catch (err) {
      setError(err.message || "Unable to delete task.");
      setTasks(previousTasks);
    }
  }

  async function handleSaveEdit(id, payload) {
    const previousTasks = [...tasks];
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, ...payload } : t)));
    try {
      const updated = await updateTask(id, payload);
      setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
      setEditingTask(null);
    } catch (err) {
      setError(err.message || "Unable to update task.");
      setTasks(previousTasks);
    }
  }

  function handleDragStart(e, id) {
    setDraggingId(id);
    e.dataTransfer.setData("text/plain", String(id));
    e.dataTransfer.effectAllowed = "move";
  }

  function handleDragEnter(status) {
    setDragOverStatus(status);
  }

  function handleDragLeave() {
    setDragOverStatus(null);
  }

  async function handleDrop(status, e) {
    e.preventDefault();
    const idStr = draggingId ?? e.dataTransfer.getData("text/plain");
    const id = parseInt(idStr, 10);
    const task = tasks.find((t) => t.id === id);
    setDragOverStatus(null);
    setDraggingId(null);
    if (!task || task.status === status) return;
    await handleStatusChange(task, status);
  }

  const tasksTodo = tasks.filter((t) => t.status === "TODO");
  const tasksDoing = tasks.filter((t) => t.status === "DOING");
  const tasksDone = tasks.filter((t) => t.status === "DONE");

  return (
    <div className="app-root">
      {authLoading && (
        <div className="overlay">
          <div className="spinner" aria-label="Loading" />
        </div>
      )}
      <header className="app-header">
        <div>
          <h1 className="app-title">Team Task Board</h1>
          <p className="app-subtitle">
            A simple board for keeping your personal tasks organized.
          </p>
        </div>
        {user && (
          <div className="auth-meta">
            <span className="auth-user">{user.email}</span>
            <button className="ghost-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )}
      </header>

      <main className="app-main">
        {!user ? (
          <AuthForm
            mode={authMode}
            onModeChange={setAuthMode}
            onSubmit={handleAuthSubmit}
            loading={authLoading}
            error={authError}
            fieldErrors={authFieldErrors}
          />
        ) : (
          <>
            <section className="panel">
              <div className="panel-head">
                <h2 className="panel-title">Create a new task</h2>
                <p className="panel-subtitle">Set the basics; you can refine later.</p>
              </div>
              <TaskForm
                onSubmit={handleCreateTask}
                loading={creating}
                error={taskFormError}
              />
            </section>

            <section className="board">
              {loading && <div className="info-box">Loading tasks...</div>}
              {error && <div className="error-box">{error}</div>}

              {!loading && !error && (
                <div className="board-columns">
                  <TaskColumn
                    title="To Do"
                    status="TODO"
                    tasks={tasksTodo}
                    onStatusChange={handleStatusChange}
                    onEdit={setEditingTask}
                    onRequestDelete={setDeleteTarget}
                    onDragStart={handleDragStart}
                    onDropStatus={handleDrop}
                    onDragEnterStatus={handleDragEnter}
                    onDragLeaveStatus={handleDragLeave}
                    dragOverStatus={dragOverStatus}
                  />
                  <TaskColumn
                    title="Doing"
                    status="DOING"
                    tasks={tasksDoing}
                    onStatusChange={handleStatusChange}
                    onEdit={setEditingTask}
                    onRequestDelete={setDeleteTarget}
                    onDragStart={handleDragStart}
                    onDropStatus={handleDrop}
                    onDragEnterStatus={handleDragEnter}
                    onDragLeaveStatus={handleDragLeave}
                    dragOverStatus={dragOverStatus}
                  />
                  <TaskColumn
                    title="Done"
                    status="DONE"
                    tasks={tasksDone}
                    onStatusChange={handleStatusChange}
                    onEdit={setEditingTask}
                    onRequestDelete={setDeleteTarget}
                    onDragStart={handleDragStart}
                    onDropStatus={handleDrop}
                    onDragEnterStatus={handleDragEnter}
                    onDragLeaveStatus={handleDragLeave}
                    dragOverStatus={dragOverStatus}
                  />
                </div>
              )}
            </section>
          </>
        )}
      </main>

      {editingTask && (
        <EditTaskModal
          task={editingTask}
          onClose={() => setEditingTask(null)}
          onSave={handleSaveEdit}
        />
      )}
      {deleteTarget && (
        <ConfirmDeleteModal
          task={deleteTarget}
          onCancel={() => setDeleteTarget(null)}
          onConfirm={async () => {
            await handleDelete(deleteTarget.id);
            setDeleteTarget(null);
          }}
        />
      )}
    </div>
  );
}

function AuthForm({ mode, onModeChange, onSubmit, loading, error, fieldErrors }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [localError, setLocalError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setLocalError("Email and password are required.");
      return;
    }
    setLocalError("");
    onSubmit({ email, password, username });
  }

  const renderError = (msg) =>
    msg ? <div className="error-text">{msg}</div> : null;

  return (
    <section className="panel auth-panel">
      <div className="auth-toggle">
        <button
          type="button"
          className={mode === "login" ? "tab active" : "tab"}
          onClick={() => onModeChange("login")}
        >
          Login
        </button>
        <button
          type="button"
          className={mode === "register" ? "tab active" : "tab"}
          onClick={() => onModeChange("register")}
        >
          Register
        </button>
      </div>

      <form className="task-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-field full-width">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
            />
            {renderError(fieldErrors?.email)}
          </div>
        </div>
        {mode === "register" && (
          <div className="form-row">
            <div className="form-field full-width">
              <label>Username (optional)</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Used for display only"
              />
              {renderError(fieldErrors?.username)}
            </div>
          </div>
        )}
        <div className="form-row">
          <div className="form-field full-width">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="At least 8 characters"
            />
            {renderError(fieldErrors?.password)}
          </div>
        </div>
        {(error || localError || fieldErrors?.general) && (
          <div className="error-box inline-error">
            {error || fieldErrors?.general || localError}
          </div>
        )}
        <div className="form-actions">
          <button type="submit" disabled={loading || !email || !password}>
            {loading ? "Please wait..." : mode === "login" ? "Login" : "Register"}
          </button>
        </div>
      </form>
    </section>
  );
}

function TaskForm({ onSubmit, loading, error }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [dueDate, setDueDate] = useState("");
  const [description, setDescription] = useState("");
  const [localError, setLocalError] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) {
      setLocalError("Title is required.");
      return;
    }

    onSubmit({
      title: title.trim(),
      description: description.trim(),
      priority,
      status: "TODO",
      due_date: dueDate || null,
    });

    setLocalError("");
    setTitle("");
    setDescription("");
    setPriority("MEDIUM");
    setDueDate("");
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="form-field">
          <label>Task title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="What needs to be done?"
          />
        </div>
        <div className="form-field">
          <label>Priority</label>
          <select
            className="select"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
          >
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </div>
        <div className="form-field">
          <label>Due date</label>
          <input
            type="date"
            className="date-input"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>
      </div>
      <div className="form-row">
        <div className="form-field full-width">
          <label>Description</label>
          <textarea
            rows="2"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a short note..."
          />
        </div>
      </div>
      {(error || localError) && (
        <div className="error-box inline-error">{error || localError}</div>
      )}
      <div className="form-actions">
        <button type="submit" disabled={loading || !title.trim()}>
          {loading ? "Saving..." : "Add task"}
        </button>
      </div>
    </form>
  );
}

function TaskColumn({
  title,
  status,
  tasks,
  onStatusChange,
  onEdit,
  onRequestDelete,
  onDragStart,
  onDropStatus,
  onDragEnterStatus,
  onDragLeaveStatus,
  dragOverStatus,
}) {
  return (
    <div
      className={`column ${
        dragOverStatus === status ? "column-dropping" : ""
      }`}
      data-status={status}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => onDropStatus(status, e)}
      onDragEnter={() => onDragEnterStatus(status)}
      onDragLeave={onDragLeaveStatus}
    >
      <div className="column-header">
        <h3>{title}</h3>
        <span className="column-count">{tasks.length}</span>
      </div>
      <div className="column-body">
        {tasks.length === 0 && (
          <p className="column-empty">Nothing here yet.</p>
        )}
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onStatusChange={onStatusChange}
            onEdit={onEdit}
            onRequestDelete={onRequestDelete}
            onDragStart={onDragStart}
          />
        ))}
      </div>
    </div>
  );
}

function TaskCard({
  task,
  onStatusChange,
  onEdit,
  onRequestDelete,
  onDragStart,
}) {
  const priorityClass = `badge badge-${task.priority.toLowerCase()}`;

  return (
    <article
      className="task-card"
      draggable
      onDragStart={(e) => onDragStart(e, task.id)}
    >
      <header className="task-card-header">
        <h4>{task.title}</h4>
        <span className={priorityClass}>
          {PRIORITY_LABELS[task.priority] || task.priority}
        </span>
      </header>
      {task.description && (
        <p className="task-card-description">{task.description}</p>
      )}
      {task.due_date && (
        <div className="task-meta task-meta-date">
          <span className="task-meta-item">Due: {task.due_date}</span>
        </div>
      )}
      <footer className="task-card-footer">
        <div className="task-actions">
          <div className="status-group">
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={
                  value === task.status ? "status-button active" : "status-button"
                }
                data-status={value}
                onClick={() => onStatusChange(task, value)}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="action-group">
            <button
              type="button"
              className="icon-chip"
              onClick={() => onEdit(task)}
              aria-label="Edit task"
            >
              {"✎"}
            </button>
            <button
              type="button"
              className="icon-chip danger"
              onClick={() => onRequestDelete(task)}
              aria-label="Delete task"
            >
              {"🗑"}
            </button>
          </div>
        </div>
      </footer>
    </article>
  );
}
function EditTaskModal({ task, onClose, onSave }) {
  const [title, setTitle] = useState(task.title || "");
  const [priority, setPriority] = useState(task.priority || "MEDIUM");
  const [status, setStatus] = useState(task.status || "TODO");
  const [dueDate, setDueDate] = useState(task.due_date || "");
  const [description, setDescription] = useState(task.description || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSave(e) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    setSaving(true);
    setError("");
    await onSave(task.id, {
      title: title.trim(),
      priority,
      status,
      due_date: dueDate || null,
      description: description.trim(),
    });
    setSaving(false);
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Edit task</h3>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <form className="task-form" onSubmit={handleSave}>
          <div className="form-row">
            <div className="form-field">
              <label>Task title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
            </div>
            <div className="form-field">
              <label>Status</label>
              <select
                className="select"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="TODO">To Do</option>
                <option value="DOING">Doing</option>
                <option value="DONE">Done</option>
              </select>
            </div>
            <div className="form-field">
              <label>Priority</label>
              <select
                className="select"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-field">
              <label>Due date</label>
              <input
                type="date"
                className="date-input"
                value={dueDate || ""}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
            <div className="form-field full-width">
              <label>Description</label>
              <textarea
                rows="3"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          {error && <div className="error-box inline-error">{error}</div>}
          <div className="form-actions modal-actions">
            <button
              type="button"
              className="ghost-button"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ConfirmDeleteModal({ task, onCancel, onConfirm }) {
  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Delete task</h3>
          <button className="icon-button" onClick={onCancel} aria-label="Close">
            ×
          </button>
        </div>
        <div className="modal-body">
          <p>
            Are you sure you want to delete <strong>{task.title}</strong>?
            This cannot be undone.
          </p>
        </div>
        <div className="form-actions modal-actions">
          <button type="button" className="ghost-button" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="delete-button" onClick={onConfirm}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;



