# Horse Racing Edge Dashboard Setup Guide

This guide will walk you through setting up and running the dashboard step-by-step. 

**Verified Prerequisites:**
- Node.js (v24.13.0)
- Python (v3.14.3)
- Xcode Command Line Tools (Installed)

---

## Part 1: Backend Setup (Python)

Open your terminal and run these commands **one by one**:

1. **Navigate to the backend folder**:
   ```bash
   cd /Users/ron/Documents/Antigravity/horse-racing-dashboard/backend
   ```

2. **Create a virtual environment** (this isolates dependencies):
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```
   *(Your terminal prompt should now show `(venv)` at the start)*.

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install the browser for the scraper**:
   ```bash
   playwright install chromium
   ```

6. **Start the Backend Server**:
   ```bash
   uvicorn main:app --reload
   ```
   
   **Success Check:** You should see output saying `Uvicorn running on http://127.0.0.1:8000`.
   *Keep this terminal window open and running.*

---

## Part 2: Frontend Setup (Next.js)

Open a **new** terminal window (leave the backend running in the first one).

1. **Navigate to the frontend folder**:
   ```bash
   cd /Users/ron/Documents/Antigravity/horse-racing-dashboard/frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Frontend Dashboard**:
   ```bash
   npm run dev
   ```

   **Success Check:** You should see output saying `Ready in 2.5s` and `http://localhost:3000`.

---

## Part 3: Using the Dashboard

1. Open your web browser to [http://localhost:3000](http://localhost:3000).
2. Find a live race on Zeturf (e.g., `https://www.zeturf.fr/en/course/...`).
3. Paste the URL into the "Enter Zeturf Race URL" box on your dashboard.
4. Click **Monitor Race**.
5. Wait ~10 seconds for the data to appear.

---

## Troubleshooting

- **Error: "address already in use"**: 
  - Stop any existing servers (Ctrl+C).
  - Check if something else is using port 3000 or 8000.

- **Error: "Module not found" in Python**:
  - Ensure you ran `source venv/bin/activate` *before* running `uvicorn`.

- **Error: "playwright not found"**:
  - Run `pip install playwright && playwright install chromium` again inside the active venv.
