# LinkedIn Engagement Agent

This is a local browser automation tool designed to interact with your LinkedIn feed automatically. It uses Playwright to connect to your existing Chrome profile and scroll through your feed, liking and optionally commenting on relevant posts. It is designed to run locally and keep your account safe by using human-like delays and enforcing strict guardrails.

## Features
- **Local Browser Integration**: Connects to your existing Google Chrome user data directory so you don't need to pass your login credentials.
- **Smart Filtering**: Uses AI to determine if a post is relevant to your interests.
- **Auto-drafted Comments**: Generates personalized, concise comments using AI.
- **Human-in-the-loop**: Requires manual approval for comments to ensure accuracy and personal touch.
- **Strict Guardrails**: Automatically limits activity (e.g., max 20 connections, 40 reactions per day) to avoid triggering LinkedIn's spam filters.

## Prerequisites

- Python 3.8+
- [Playwright for Python](https://playwright.dev/python/)
- Google Chrome installed locally

### Setup

1. Clone or download this repository.
2. Install the required Python packages:
   ```bash
   pip install playwright requests
   playwright install chromium
   ```

## Configuration

By default, the script looks for your Chrome profile at `~/.config/google-chrome` (Linux). If you're on a different OS or using a non-default profile path, you must edit `linkedin_agent.py` and modify the `USER_DATA_DIR` variable inside `main()`.

Make sure all Chrome instances are completely closed before running the script so Playwright can attach to the profile.

## AI Configuration: Local vs. API

This agent uses AI for filtering posts and generating comments. It supports two modes:

### Option 1: Local AI via Ollama (Default)
By default, the script will attempt to connect to a locally running instance of [Ollama](https://ollama.com/) with the `granite4.1:8b` model.
1. Install Ollama and start the service.
2. Pull the model: `ollama run granite4.1:8b`
3. Run the agent.

### Option 2: OpenAI API
If you prefer not to run a local model, you can use the OpenAI API. The script will automatically use OpenAI if it detects an `OPENAI_API_KEY` environment variable.

1. Get an API key from [OpenAI](https://platform.openai.com/).
2. Set it as an environment variable before running the script:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
3. Run the script. The agent will automatically use `gpt-4o-mini` for all operations.

## Usage

To start the agent, run:

```bash
python linkedin_agent.py
```

The script will launch a browser window, navigate to LinkedIn, and begin scrolling through your feed. It will output its findings to the console. When it finds a relevant post, it will prompt you in the terminal to approve, edit, or skip the AI-generated comment.

## Safety & Compliance

- **Do NOT** remove the human delays (`time.sleep`) in the script. These are critical for avoiding detection.
- **Do NOT** increase the daily limits above a safe threshold.
- Always monitor the agent's behavior during its first few runs to ensure it aligns with your expectations.
