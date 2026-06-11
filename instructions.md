# Agent Directives: LinkedIn Automation

- **Primary Goal:** Assist in creating a safe browser-automation pipeline.
- **Safety Rule 1:** All automation must utilize local browser profiles (via Playwright or Selenium) to reuse active login session cookies. Do not script manual credential inputs.
- **Safety Rule 2:** Enforce randomized, human-like pacing between all actions (`time.sleep(random.uniform(5.0, 15.0))`).
- **Safety Rule 3:** Cap active automated operations to a strict limit of 15 connections or 30 reactions per run.
