import os
import time
from django.conf import settings
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

def get_cookie_path(username):
    """
    Returns path to the session cookies JSON file for the account.
    """
    cookie_dir = os.path.join(settings.BASE_DIR, "session_cookies")
    os.makedirs(cookie_dir, exist_ok=True)
    return os.path.join(cookie_dir, f"{username}.json")

def is_logged_in(page: Page) -> bool:
    """
    Checks if the session is currently logged in.
    """
    try:
        page.goto("https://www.instagram.com/", timeout=20000)
        time.sleep(3)
        # If we see elements like the "Search" or "Direct" or "New Post" buttons, we're logged in.
        # Instagram's mobile layout has 'svg[aria-label="Direct"]' or 'a[href="/direct/inbox/"]'
        logged_in_selectors = [
            'svg[aria-label="New Post"]', 
            'svg[aria-label="Direct"]', 
            'a[href="/explore/"]',
            'a[href="/direct/inbox/"]'
        ]
        for selector in logged_in_selectors:
            if page.locator(selector).count() > 0:
                return True
        return False
    except Exception:
        return False

def instagram_login(page: Page, username, password, logger=print) -> bool:
    """
    Logs in to Instagram. Reuses session cookies if available.
    """
    cookie_path = get_cookie_path(username)
    
    # Check if we can reuse cookie state (should be loaded when context is created)
    if os.path.exists(cookie_path):
        logger(f"[LOGIN] Cookie state found for @{username}. Checking session validity...")
        if is_logged_in(page):
            logger(f"[LOGIN] Session cookie is valid. Logged in as @{username} without password.")
            return True
        else:
            logger(f"[LOGIN] Session cookie expired or invalid. Re-authenticating...")

    # Log in manually
    try:
        logger(f"[LOGIN] Navigating to Instagram login...")
        page.goto("https://www.instagram.com/accounts/login/", timeout=30000)
        time.sleep(2)
        
        # Fill username
        page.wait_for_selector('input[name="username"]', timeout=10000)
        page.fill('input[name="username"]', username)
        time.sleep(0.5)
        
        # Fill password
        page.fill('input[name="password"]', password)
        time.sleep(0.5)
        
        # Click login
        page.click('button[type="submit"]')
        
        # Wait for login redirect/landing (look for "Save Info" or home feed elements)
        logger("[LOGIN] Waiting for login credentials submission...")
        page.wait_for_timeout(6000)
        
        # Check if login succeeded
        if is_logged_in(page):
            logger(f"[LOGIN] Manually logged in as @{username}. Saving session cookies...")
            page.context.storage_state(path=cookie_path)
            return True
        else:
            logger(f"[LOGIN] Could not verify login success for @{username}.")
            return False
            
    except Exception as e:
        logger(f"[LOGIN] Error during manual authentication: {e}")
        return False

def follow_user(page: Page, target_username: str, logger=print) -> bool:
    """
    Navigates to user profile and performs Follow action.
    """
    logger(f"[ACTION] Navigating to profile @{target_username} to follow...")
    page.goto(f"https://www.instagram.com/{target_username}/", timeout=30000)
    time.sleep(3)
    
    try:
        # Try multiple selector patterns for "Follow"
        follow_selectors = [
            'button:has-text("Follow")', 
            'button:text-is("Follow")', 
            'div[role="button"]:has-text("Follow")'
        ]
        
        button = None
        for selector in follow_selectors:
            loc = page.locator(selector)
            if loc.count() > 0:
                button = loc.first
                break
                
        if button:
            # Check if already followed (e.g. text says "Following" or "Message")
            btn_text = button.text_content()
            if "Following" in btn_text or "Requested" in btn_text:
                logger(f"[ACTION] Already following or requested @{target_username}.")
                return True
                
            button.click()
            time.sleep(2)
            logger(f"[ACTION] Clicked Follow on @{target_username}.")
            return True
        else:
            logger(f"[ACTION] Follow button not found on @{target_username}'s profile. Maybe already following.")
            return False
    except Exception as e:
        logger(f"[ACTION] Failed to follow @{target_username}: {e}")
        return False

def like_latest_post(page: Page, target_username: str, logger=print) -> bool:
    """
    Navigates to profile, opens latest post, and likes it.
    """
    logger(f"[ACTION] Navigating to @{target_username} to like post...")
    page.goto(f"https://www.instagram.com/{target_username}/", timeout=30000)
    time.sleep(3)
    
    try:
        # Click the first post in the grid
        # Mobile layout first post selector is typically: a[href^="/p/"]
        post_locator = page.locator('a[href^="/p/"]').first
        if post_locator.count() > 0:
            post_locator.click()
            time.sleep(3)
            
            # Click the Like SVG/Button
            # Instagram post Like button has aria-label="Like"
            like_selectors = [
                'svg[aria-label="Like"]',
                'button:has(svg[aria-label="Like"])'
            ]
            
            liked = False
            for selector in like_selectors:
                loc = page.locator(selector)
                if loc.count() > 0:
                    loc.first.click()
                    liked = True
                    break
            
            if liked:
                logger(f"[ACTION] Liked latest post from @{target_username}.")
                time.sleep(2)
                return True
            else:
                logger(f"[ACTION] Like button not found or already liked.")
                return False
        else:
            logger(f"[ACTION] No posts found on @{target_username}'s feed.")
            return False
    except Exception as e:
        logger(f"[ACTION] Failed to like latest post: {e}")
        return False

def comment_on_post(page: Page, target_username: str, message: str, logger=print) -> bool:
    """
    Navigates to profile, opens latest post, and comments.
    """
    logger(f"[ACTION] Navigating to @{target_username} to comment...")
    page.goto(f"https://www.instagram.com/{target_username}/", timeout=30000)
    time.sleep(3)
    
    try:
        post_locator = page.locator('a[href^="/p/"]').first
        if post_locator.count() > 0:
            post_locator.click()
            time.sleep(3)
            
            # Click comment button to focus comment input on mobile or locate textarea
            comment_input_selectors = [
                'textarea[aria-label="Add a comment..."]',
                'textarea[placeholder="Add a comment..."]',
                'textarea'
            ]
            
            textarea = None
            for selector in comment_input_selectors:
                loc = page.locator(selector)
                if loc.count() > 0:
                    textarea = loc.first
                    break
                    
            if textarea:
                textarea.click()
                textarea.fill(message)
                time.sleep(1)
                
                # Click post button
                post_button = page.locator('button:has-text("Post")').first
                if post_button.count() > 0:
                    post_button.click()
                    logger(f"[ACTION] Posted comment on @{target_username}: \"{message}\"")
                    time.sleep(2)
                    return True
                else:
                    # Press Enter key as fallback
                    textarea.press("Enter")
                    logger(f"[ACTION] Submitted comment via Enter key on @{target_username}.")
                    time.sleep(2)
                    return True
            else:
                logger(f"[ACTION] Comment textarea not found.")
                return False
        else:
            logger(f"[ACTION] No posts found to comment on @{target_username}'s feed.")
            return False
    except Exception as e:
        logger(f"[ACTION] Failed to comment on post: {e}")
        return False
