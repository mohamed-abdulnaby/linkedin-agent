import time
import random
import requests
import json
import os
from playwright.sync_api import sync_playwright

# Guardrails state
actions_state = {
    'connections_sent_today': 0,
    'reactions_made_today': 0
}

MAX_CONNECTIONS_PER_DAY = 20
MAX_REACTIONS_PER_DAY = 40

def human_delay():
    """Always include a random human delay between browser actions."""
    delay = random.uniform(5.0, 15.0)
    print(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)

def ask_ollama(text):
    """Ask local Ollama to filter if the post is relevant to tech/engineering."""
    url = "http://localhost:11434/api/generate"
    
    prompt = f"Analyze the following LinkedIn post. First, if it is a job posting, recruitment ad, or advertising an open job offer, you MUST answer NO. Otherwise, determine if it matches ANY of these criteria: 1) Someone celebrating being hired or getting a promotion. 2) The telecommunications (telecom) industry. 3) Java or general programming. If it matches at least one criteria, answer YES. Otherwise, answer NO. Answer ONLY with YES or NO.\n\nPost: {text}"
    
    payload = {
        "model": "granite4.1:8b",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json().get('response', '').strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return False

def generate_draft_with_ollama(post_text):
    """Use local Ollama to draft a short, personalized connection note or comment."""
    url = "http://localhost:11434/api/generate"
    prompt = f"Draft a hyper-concise LinkedIn comment for this tech post. Max 30 characters (4-6 words). NO hashtags. Example: 'Great work!' or 'Love this update!'. Only output the comment text.\n\nPost: {post_text}"
    
    payload = {
        "model": "granite4.1:8b",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('response', '').strip()
    except Exception as e:
        print(f"Error calling Ollama for draft: {e}")
        return None

def ask_openai(text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    prompt = f"Analyze the following LinkedIn post. First, if it is a job posting, recruitment ad, or advertising an open job offer, you MUST answer NO. Otherwise, determine if it matches ANY of these criteria: 1) Someone celebrating being hired or getting a promotion. 2) The telecommunications (telecom) industry. 3) Java or general programming. If it matches at least one criteria, answer YES. Otherwise, answer NO. Answer ONLY with YES or NO.\n\nPost: {text}"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()['choices'][0]['message']['content'].strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return False

def generate_draft_with_openai(post_text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    prompt = f"Draft a hyper-concise LinkedIn comment for this tech post. Max 30 characters (4-6 words). NO hashtags. Example: 'Great work!' or 'Love this update!'. Only output the comment text.\n\nPost: {post_text}"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI for draft: {e}")
        return None

def ask_ai(text):
    if os.environ.get("OPENAI_API_KEY"):
        return ask_openai(text)
    return ask_ollama(text)

def generate_draft_with_ai(post_text):
    if os.environ.get("OPENAI_API_KEY"):
        return generate_draft_with_openai(post_text)
    return generate_draft_with_ollama(post_text)

def main():
    # Set this to your actual Chrome user data directory path
    # Usually: '~/.config/google-chrome' on Linux
    USER_DATA_DIR = os.path.expanduser("~/.config/google-chrome")
    
    with sync_playwright() as p:
        print("Launching browser with user profile...")
        # Launch persistent context to keep session logged in
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,   # Keeping headless=False is safer for detection avoidance
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Close the default blank page that opens with context and create a fresh one
        if len(browser.pages) > 0:
            page = browser.pages[0]
        else:
            page = browser.new_page()
            
        human_delay()
        
        url_to_scrape = "https://www.linkedin.com/feed/"
        print(f"Navigating to {url_to_scrape}")
        page.goto(url_to_scrape, timeout=60000)
        human_delay()
        
        print("Waiting for posts to load...")
        try:
            # LinkedIn selectors change frequently, adjusting if necessary based on current UI
            page.wait_for_selector('.feed-shared-update-v2', timeout=15000)
        except Exception as e:
            print("Could not find posts, UI might have changed or page load was slow.")
            browser.close()
            return
            
        processed_posts = set()
        
        while actions_state['reactions_made_today'] < MAX_REACTIONS_PER_DAY and actions_state['connections_sent_today'] < MAX_CONNECTIONS_PER_DAY:
            posts = page.query_selector_all('.feed-shared-update-v2')
            
            for post in posts:
                if actions_state['reactions_made_today'] >= MAX_REACTIONS_PER_DAY or actions_state['connections_sent_today'] >= MAX_CONNECTIONS_PER_DAY:
                    break
                    
                # Extract text from the post description
                text_element = post.query_selector('.feed-shared-update-v2__description')
                if text_element:
                    post_text = text_element.inner_text().strip()
                    if not post_text or post_text in processed_posts:
                        continue
                        
                    processed_posts.add(post_text)
                    
                    # Extract author name for context
                    author_element = post.query_selector('.update-components-actor__name') or post.query_selector('.feed-shared-actor__name') or post.query_selector('span[dir="ltr"]')
                    author_name = author_element.inner_text().strip() if author_element else "Unknown Author"
                    
                    print(f"\n--- Found Relevant Post by {author_name} ---")
                    
                    # Check relevance with AI
                    is_relevant = ask_ai(post_text)
                    
                    if is_relevant:
                        print("Status: RELEVANT. Generating response...")
                        draft = generate_draft_with_ai(post_text)
                        if draft:
                            # Human-in-the-loop confirmation with rich context
                            print("\n==================================================")
                            print(f"👤 AUTHOR: {author_name}")
                            print(f"📄 POST: {post_text[:200]}...")
                            print(f"🤖 DRAFT: {draft}")
                            print("==================================================")
                            user_input = input("Press [Enter] to approve this comment, type a new comment to edit it, or type 'skip' to ignore: ").strip()
                        
                        if user_input.lower() == 'skip':
                            print("Skipping post based on your input.")
                        else:
                            final_comment = user_input if user_input else draft
                            print(f"✅ Final Comment to post: {final_comment}")
                            
                            # -------------------------------------------------------------
                            # Interaction Logic (Active)
                            # -------------------------------------------------------------
                            # The post element might detach from the DOM during the wait for user input.
                            # We attempt to re-locate it if necessary.
                            try:
                                post.scroll_into_view_if_needed(timeout=2000)
                                current_post = post
                            except Exception:
                                print("⚠️ Post detached. Re-locating by text...")
                                snippet = post_text[:50].replace('"', '').replace("'", "")
                                try:
                                    loc = page.locator('.feed-shared-update-v2').filter(has_text=snippet).first
                                    loc.wait_for(timeout=5000)
                                    loc.scroll_into_view_if_needed(timeout=2000)
                                    current_post = loc.element_handle()
                                except Exception as e:
                                    print(f"❌ Could not re-locate post: {e}")
                                    continue

                            if not current_post:
                                print("❌ Could not re-locate post. Skipping.")
                                continue

                            # 1. Like the post
                            like_btn = current_post.query_selector('button[aria-pressed="false"].react-button__trigger')
                            if like_btn:
                                try:
                                    like_btn.click()
                                    actions_state['reactions_made_today'] += 1
                                    print("Liked the post!")
                                    human_delay()
                                except Exception as e:
                                    print(f"Could not click like button: {e}")
                            
                            # 2. Click comment button to open text box
                            # The first button with the text "Comment" is the action button on the post header
                            comment_btn = current_post.query_selector('button[aria-label*="Comment"]') or current_post.query_selector('button:has-text("Comment")')
                            if comment_btn:
                                print("Opening comment box...")
                                try:
                                    comment_btn.click(force=True)
                                    human_delay()
                                except Exception as e:
                                    print(f"Could not click comment button: {e}")
                                
                                # 3. Type the comment (Using keyboard.type to trigger LinkedIn's React listeners)
                                textbox = current_post.query_selector('div.ql-editor') or current_post.query_selector('div[role="textbox"]') or current_post.query_selector('.comments-comment-box__editor')
                                if textbox:
                                    print("Typing comment...")
                                    try:
                                        textbox.click()  # Focus the box first
                                        page.keyboard.type(final_comment)
                                        human_delay()
                                    except Exception as e:
                                        print(f"Could not type comment: {e}")
                                    
                                    # 4. Hit Submit
                                    print("Attempting to hit submit via JavaScript...")
                                    try:
                                        # Evaluate JS to find the last button with text "Comment" or "Post" inside the post box
                                        clicked = current_post.evaluate('''
                                            (postNode) => {
                                                const buttons = Array.from(postNode.querySelectorAll('button'));
                                                const submitBtns = buttons.filter(b => {
                                                    const text = b.innerText ? b.innerText.trim() : '';
                                                    return text === 'Comment' || text === 'Post';
                                                });
                                                if (submitBtns.length > 0) {
                                                    // The last one is the submit button inside the comment box
                                                    const target = submitBtns[submitBtns.length - 1];
                                                    
                                                    // Forcefully remove the disabled attribute in case React hasn't caught up
                                                    target.removeAttribute('disabled');
                                                    target.disabled = false; 
                                                    
                                                    target.click();
                                                    return true;
                                                }
                                                return false;
                                            }
                                        ''')
                                        
                                        if clicked:
                                            print("Comment posted successfully!")
                                        else:
                                            print("Submit button not found via JS. Attempting Tab+Enter...")
                                            page.keyboard.press("Tab")
                                            page.keyboard.press("Enter")
                                            
                                    except Exception as e:
                                        print(f"Failed to submit: {e}")
                                else:
                                    print("ERROR: Could not find the comment text box.")
                            else:
                                print("ERROR: Could not find the 'Comment' button on the post.")
                                
                            # 5. Connect (Plain request)
                            connect_btn = current_post.query_selector('button:has-text("Connect")')
                            if connect_btn and actions_state['connections_sent_today'] < MAX_CONNECTIONS_PER_DAY:
                                print("Found 'Connect' button on post. Sending plain connection request...")
                                try:
                                    connect_btn.click(force=True)
                                    human_delay()
                                    
                                    # Handle "Send without a note" modal if it appears
                                    send_without_note_btn = page.query_selector('button:has-text("Send without a note")')
                                    if send_without_note_btn and send_without_note_btn.is_visible():
                                        print("Clicking 'Send without a note' on modal...")
                                        send_without_note_btn.click(force=True)
                                        human_delay()
                                        
                                    actions_state['connections_sent_today'] += 1
                                    print(f"Connection request sent! Total today: {actions_state['connections_sent_today']}")
                                except Exception as e:
                                    print(f"Failed to send connection request: {e}")
                            # ALWAYS include human delay after actions
                            human_delay() 
                            # -------------------------------------------------------------
                    else:
                        print("Status: Not relevant. Skipping.")
                        
                # Adding a delay before checking the next post to simulate human reading/scrolling
                human_delay()
                
            if actions_state['reactions_made_today'] >= MAX_REACTIONS_PER_DAY or actions_state['connections_sent_today'] >= MAX_CONNECTIONS_PER_DAY:
                break
                
            print("\nScrolling down to load more posts...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            human_delay()

        print("\nSession complete. Closing browser.")
        browser.close()

if __name__ == "__main__":
    main()
