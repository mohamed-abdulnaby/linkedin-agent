# LinkedIn Engagement Agent

## Objective
Automate LinkedIn profile discovery and post-filtering safely using local browser automation.

## Guardrails (CRITICAL)
- Never exceed 20 connection requests or 40 post reactions per day.
- Always include a random human delay (`time.sleep(random.uniform(5.0, 15.0))`) between browser actions.
- Use the existing local Chrome user data directory to maintain an active login session; never attempt automated credential login.
