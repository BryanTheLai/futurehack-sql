# CogniQuery 🤖 — AI-Powered Data Insights

*Submission for FutureHack! A.I. Battlefield Hackathon*

[![Hackathon](https://img.shields.io/badge/FutureHack!-A.I.Battlefield-blueviolet)](https://www.futurehack.dev/)  
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)  
[![Framework](https://img.shields.io/badge/Framework-crewai-orange)](https://www.crewai.com/)  
[![UI](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)

CogniQuery empowers anyone to turn complex business questions into actionable data reports—no SQL required. Our advanced multi-agent AI system simulates a full analytics team, guiding every step from the initial question to final visualization.

![Entity Relationship Diagram](https://github.com/BryanTheLai/futurehack-sql/blob/main/images/futurehack-erd.png?raw=true)

---

### 🎥 Demo Video

**[Watch the full CogniQuery walkthrough here](https://your-video-link-here.com)**

*This video highlights the seamless performance of our multi-agent system, providing a reliable look at our app’s capabilities.*

![App UI Screenshot](https://raw.githubusercontent.com/wbryanteoh/futurehack-sql/main/screenshot.png)  
*(Tip: Replace this link with a screenshot from your own repo!)*

---

### ✨ Features at a Glance

- **Agentic AI Workflow:** Powered by `crewai`, CogniQuery uses specialized AI agents (Analyst, DBA, Scientist, Strategist) collaborating for more accurate and meaningful results than traditional text-to-SQL.
- **Ask in Plain English:** Simply ask questions like “How did we do last month?” and get a complete report with charts in seconds.
- **Smart Visualizations:** Automatically generates the right chart type to illuminate your data.
- **Live Activity Log:** See your AI team’s thought process, SQL queries, and scripts in real time—building transparency and trust.
- **Bring Your Own Database:** Securely connect to your own NeonDB-compatible database. Your data stays private.

---

### 🧠 Architecture: How the AI Team Works

CogniQuery’s strength lies in its structured, sequential agent workflow. Each agent has a distinct responsibility and hands off to the next, just like a high-performing analytics team.

Here’s a look at the information flow and agent collaboration:

![AI Team Workflow Diagram](https://raw.githubusercontent.com/BryanTheLai/futurehack-sql/main/images/graphviz.png)

---

### 💻 Tech Stack

| Category      | Technology                                                                                                                                                                                                |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **AI Agents** | ![CrewAI](https://img.shields.io/badge/crewAI-Framework-orange) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-42b38f) ![Gemini](https://img.shields.io/badge/Google-Gemini_Pro-4285F4)             |
| **Frontend**  | ![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b)                                                                                                                                            |
| **Database**  | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-336791)                                                                                                                                      |
| **Data Tools**| ![Pandas](https://img.shields.io/badge/Pandas-Library-150458) ![Matplotlib](https://img.shields.io/badge/Matplotlib-Library-8a2be2)                                                                       |

---

### 🛠️ Getting Started

Run CogniQuery locally in just a few steps:

1. **Clone this repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. **Set up your Python environment:**
    - **Windows:**
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    - **macOS / Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3. **Install project dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Configure environment variables:**
    Copy the example file and add your keys:
    ```bash
    # Windows
    copy .env.example .env

    # macOS / Linux
    cp .env.example .env
    ```
    Then edit `.env`:
    ```env
    OPENAI_API_KEY="sk-..."
    GEMINI_API_KEY="..."
    NEONDB_CONN_STR="postgresql://user:password@host:port/dbname"
    ```
    *Or enter these directly in the app sidebar.*

5. **Launch the app:**
    ```bash
    streamlit run app.py
    ```
    Your browser will launch CogniQuery automatically!

---

Let me know if you want any further customization or adjustments!
