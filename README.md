# AI-Powered Cold Email Generator

This project generates personalized cold outreach emails using OpenAI models. It leverages a modular structure, fetches data from a database, and logs generation results.

## Features

*   Generates personalized email drafts based on product information and target recipient details.
*   Utilizes OpenAI's reasoning (`o1`) and web search (`gpt-4o`) capabilities.
*   Supports fetching product information from local email files or via web search.
*   Implements multiple email improvement strategies:
    *   Baseline generation.
    *   Structured summary generation.
    *   First draft generation with constraints.
    *   One-shot improvement using a reference email.
    *   Zero-shot improvement using predefined advice.
*   Uses SQLite database (via Peewee ORM) to store:
    *   Client configuration (product details, reference emails, advice templates).
    *   Prompt templates for different generation stages.
    *   Detailed logs of each email generation run, including outputs for every stage.
*   Modular code structure (`src` directory) for better organization and maintainability.
*   Configuration managed via `.env` file and `src/config.py`.

## Project Structure

```
.
├── .env                      # Environment variables (API Key)
├── email_generator.db        # SQLite database file (created by setup)
├── requirements.txt          # Python dependencies
├── setup_database.py         # Script to initialize/reset the database
├── emails/                   # Directory for storing input email files
│   └── [product_name].txt
├── src/
│   ├── __init__.py
│   ├── config.py             # Core configuration and flags
│   ├── data_handler.py       # Functions for reading input data (e.g., emails)
│   ├── main.py               # Main application entry point and pipeline orchestration
│   ├── openai_client.py      # Wrapper for OpenAI API calls
│   ├── processors.py         # Core logic for each generation stage
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py         # Peewee ORM database models
│   └── prompts/              # Directory for prompt templates
│       ├── __init__.py
│       ├── baseline_email/
│       ├── first_draft/
│       ├── one_shot_improvement/
│       ├── product_description/
│       ├── summary/
│       ├── target_description/
│       └── zero_shot_improvement/
└── README.md                 # This file
```

## Setup Instructions

**1. Prerequisites:**

*   Python 3.8 or higher installed.
*   Git (optional, for cloning).
*   An OpenAI API Key.

**2. Create Environment File:**

*   Create a file named `.env` in the root directory of the project.
*   Add your OpenAI API key to this file:
    ```dotenv
    OPENAI_API_KEY=sk-your_openai_api_key_here
    ```

**3. Install Dependencies:**

*   It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
*   Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

**4. Prepare Input Email Files (If applicable):**

*   If any of your clients use the `email` source type for product information (configured during database setup or later), ensure the corresponding `.txt` files exist in the `emails/` directory in the project root. The filename should match the `product_info_detail` stored for that client (e.g., `emails/OptimizeX.txt`).

**5. Setup the Database:**

*   Run the database setup script. This will:
    *   Create the `email_generator.db` SQLite file if it doesn't exist.
    *   Create the necessary tables (`Clients`, `Prompts`, `GeneratedEmails`).
    *   **Clear any existing data** from these tables.
    *   Populate the `Prompts` table with templates found in `src/prompts/`.
    *   Add a sample client record to the `Clients` table.

    ```bash
    python setup_database.py
    ```
    *(Run this script whenever you want to reset the database prompts/clients to their initial state or after updating prompt files in `src/prompts`)*

## Running the Application

To run the email generation pipeline:

1.  Ensure your virtual environment is activated (if you created one).
2.  Navigate to the project's root directory in your terminal.
3.  Execute the main script using the `-m` flag:
    ```bash
    python -m src.main
    ```

**Process:**

*   The script currently uses hardcoded values in `src/main.py` to select the client (ID `1`) and define recipient details.
*   It connects to the database, fetches client and prompt data.
*   It runs the generation pipeline step-by-step, making API calls to OpenAI.
*   Output from each stage is printed to the console and logged to the `GeneratedEmails` table in `email_generator.db`.
*   The final selected email (based on a simple priority: One-Shot > Zero-Shot > First Draft) is printed to the console.
*   The database record for the run is updated with the final status and results.

**To Generate for Different Clients/Recipients:**

*   Modify the hardcoded values in the `if __name__ == "__main__":` block within `src/main.py`.
*   Ensure the corresponding `client_id` exists in the `Clients` table (you can add more clients manually using a DB tool or modify `setup_database.py`).

## Viewing the Database

You can inspect the contents of the `email_generator.db` file using various tools:

*   **DB Browser for SQLite:** A free, graphical tool (recommended).
*   **Command-Line `sqlite3`:**
    ```bash
    sqlite3 email_generator.db 
    sqlite> .mode column
    sqlite> .header on
    sqlite> SELECT * FROM Clients;
    sqlite> SELECT * FROM Prompts;
    sqlite> SELECT * FROM GeneratedEmails ORDER BY generation_timestamp_utc DESC LIMIT 5;
    sqlite> .quit
    ```
*   Other SQL GUI Tools (DBeaver, TablePlus, VS Code extensions, etc.). 