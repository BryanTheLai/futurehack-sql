
# CogniQuery 🤖 - Your AI Data Scientist

*Submission for the FutureHack! A.I. Battlefield Hackathon*

[![Hackathon](https://img.shields.io/badge/FutureHack!-A.I.Battlefield-blueviolet)](https://www.futurehack.dev/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-crewai-orange)](https://www.crewai.com/)
[![UI](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io/)

CogniQuery transforms complex business questions into comprehensive data reports, empowering non-technical users to unlock insights from their databases instantly. We achieve this through a sophisticated multi-agent AI system that simulates an entire data analytics team, from initial query to final visualization.

---

### 🎥 **Video Walkthrough**

**[Click here to watch the full demo of CogniQuery in action!](https://your-video-link-here.com)**

*Due to the resource-intensive nature of our multi-agent system, this video provides a smooth and reliable demonstration of our fully functional application.*

![CogniQuery UI Screenshot](https://raw.githubusercontent.com/wbryanteoh/futurehack-sql/main/screenshot.png)
*(Replace this link with a direct link to a screenshot of your app in your repo)*

---

### ✨ Key Features

-   **Agentic AI Workflow:** Powered by `crewai`, our system uses specialized AI agents (Analyst, DBA, Scientist, Strategist) that collaborate to solve problems, ensuring more robust and context-aware results than simple text-to-SQL.
-   **Natural Language to Insight:** Go from a simple question like "How did we do last month?" to a full report with charts and analysis in seconds.
-   **Automated Visualizations:** The AI Data Scientist automatically generates the most relevant chart (e.g., bar, line) to visually support the findings.
-   **Transparent Activity Log:** Watch your AI team work in real-time! Our live log shows every thought process, SQL query, and Python script as it happens, building trust and providing full transparency.
-   **Bring-Your-Own-Database (BYOD):** Securely connect to your own NeonDB-compatible database via the UI. Your data stays yours.

---

### 🧠 Architectural Deep-Dive: The AI Team Workflow

CogniQuery's power lies in its structured, sequential agentic process. Each agent has a specific role and hands off its work to the next, mimicking a real-world, high-performance data team.

This diagram illustrates the flow of information and the collaboration between the AI agents:

```graphviz
digraph CogniQueryFlow {
    rankdir=TB;
    splines=ortho;
    node [shape=box, style="rounded,filled", fontname="Arial"];

    subgraph cluster_user {
        label="User Interaction";
        style=filled;
        color=lightgrey;
        node [fillcolor=white];
        UserQuery [label="User's Question\n(e.g., 'What were our sales by region?')", shape=ellipse];
    }

    subgraph cluster_agents {
        label="CogniQuery AI Agent Crew";
        style=filled;
        color=lightblue;
        node [fillcolor=white];
        PromptEnhancer [label="🧠 Business Analyst\nRefines question using DB schema"];
        SQLGenerator [label="✍️ Database Admin\nWrites optimized SQL"];
        DataAnalyst [label="📊 Data Scientist\nAnalyzes data & creates chart"];
        ReportGenerator [label="🗣️ Comms Strategist\nBuilds final report"];
    }
    
    subgraph cluster_tools {
        label="Tools & Data";
        style=filled;
        color=lightyellow;
        node [fillcolor=white];
        DBSchema [label="Database Schema", shape=cylinder];
        DBTools [label="SQL Query Tool", shape=cylinder];
        CodeInterpreter [label="Python Interpreter\n(pandas, matplotlib)", shape=cylinder];
    }

    subgraph cluster_output {
        label="Final Output";
        style=filled;
        color=palegreen;
        node [fillcolor=white];
        FinalReport [label="Final Markdown Report\nwith embedded chart", shape=document];
    }

    # Connections
    UserQuery -> PromptEnhancer;
    PromptEnhancer -> DBSchema [label="1. Fetches schema"];
    DBSchema -> PromptEnhancer;
    PromptEnhancer -> SQLGenerator [label="2. Sends refined, schema-aware query"];
    SQLGenerator -> DataAnalyst [label="3. Sends optimized SQL query"];
    DataAnalyst -> DBTools [label="4. Executes SQL"];
    DBTools -> DataAnalyst;
    DataAnalyst -> CodeInterpreter [label="5. Runs Python analysis & viz code"];
    CodeInterpreter -> DataAnalyst;
    DataAnalyst -> ReportGenerator [label="6. Sends findings & chart path"];
    ReportGenerator -> FinalReport [label="7. Compiles & delivers report"];
}
```

---

### 💻 Tech Stack

| Category      | Technology                                                                                                                                                                                          |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **AI Agents**   | ![CrewAI](https://img.shields.io/badge/crewAI-Framework-orange) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-42b38f) ![Gemini](https://img.shields.io/badge/Google-Gemini_Pro-4285F4)    |
| **Frontend**  | ![Streamlit](https://img.shields.io/badge/Streamlit-UI-ff4b4b)                                                                                                                                      |
| **Database**  | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-336791)                                                                                                                                |
| **Data Tools**| ![Pandas](https://img.shields.io/badge/Pandas-Library-150458) ![Matplotlib](https://img.shields.io/badge/Matplotlib-Library-8a2be2)                                                                     |

---

### 🛠️ How to Run Locally

Follow these steps to set up and run CogniQuery on your local machine.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and Activate a Virtual Environment:**
    *   **Windows:**
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    *   **macOS / Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root directory by copying the example file:
    ```bash
    # For Windows
    copy .env.example .env

    # For macOS / Linux
    cp .env.example .env
    ```
    Now, open the `.env` file and add your credentials:
    ```env
    OPENAI_API_KEY="sk-..."
    GEMINI_API_KEY="..."
    NEONDB_CONN_STR="postgresql://user:password@host:port/dbname"
    ```
    *Note: You can also leave these blank and enter them directly in the Streamlit UI sidebar.*

5.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```
    Your browser should open to the CogniQuery application automatically.

```
