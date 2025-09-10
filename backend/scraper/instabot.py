import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

class InstagramCommentScraper:
    def __init__(self, headless=True, wait_time=10):
        """
        Initialize the Instagram Comment Scraper
        
        Args:
            headless (bool): Run browser in headless mode
            wait_time (int): Maximum wait time for elements
        """
        self.wait_time = wait_time
        self.setup_driver(headless)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self, headless):
        """Setup Chrome WebDriver with options"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Common options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, self.wait_time)
    
    def login(self, username, password):
        """
        Login to Instagram
        
        Args:
            username (str): Instagram username
            password (str): Instagram password
        """
        try:
            self.logger.info("Navigating to Instagram login page...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)
            
            # Accept cookies if present
            try:
                accept_cookies = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]"))
                )
                accept_cookies.click()
                time.sleep(2)
            except TimeoutException:
                self.logger.info("No cookies banner found")
            
            # Find username and password fields
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Enter credentials
            username_field.send_keys(username)
            time.sleep(1)
            password_field.send_keys(password)
            time.sleep(1)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Handle "Save Your Login Info" prompt
            try:
                not_now_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                time.sleep(2)
            except TimeoutException:
                self.logger.info("No 'Save Login Info' prompt found")
            
            # Handle notification prompt
            try:
                not_now_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now_button.click()
                time.sleep(2)
            except TimeoutException:
                self.logger.info("No notification prompt found")
            
            self.logger.info("Login successful!")
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise
    
    def navigate_to_post(self, post_url):
        """
        Navigate to a specific Instagram post
        
        Args:
            post_url (str): URL of the Instagram post
        """
        try:
            self.logger.info(f"Navigating to post: {post_url}")
            self.driver.get(post_url)
            time.sleep(3)
        except Exception as e:
            self.logger.error(f"Failed to navigate to post: {str(e)}")
            raise
    
    def load_more_comments(self, max_comments=100):
        """
        Load more comments by clicking 'Load more comments' button
        
        Args:
            max_comments (int): Maximum number of comments to load
        """
        comments_loaded = 0
        
        while comments_loaded < max_comments:
            try:
                # Look for "Load more comments" button
                load_more_button = self.driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Load more comments')]"
                )
                
                # Scroll to the button and click
                self.driver.execute_script("arguments[0].scrollIntoView();", load_more_button)
                time.sleep(1)
                load_more_button.click()
                time.sleep(2)
                
                # Count current comments using the same selector as scraping
                current_comments = len(self.driver.find_elements(
                    By.XPATH, "//span[contains(@class, 'x1lliihq')]"
                ))
                
                if current_comments > comments_loaded:
                    comments_loaded = current_comments
                    self.logger.info(f"Loaded {comments_loaded} potential comment elements")
                else:
                    break
                    
            except NoSuchElementException:
                self.logger.info("No more 'Load more comments' button found")
                break
            except Exception as e:
                self.logger.warning(f"Error loading more comments: {str(e)}")
                break
    
    def scrape_comments(self, post_url, max_comments=100):
        """
        Scrape comments from an Instagram post with UI element filtering
        
        Args:
            post_url (str): URL of the Instagram post
            max_comments (int): Maximum number of comments to scrape
            
        Returns:
            list: List of comment dictionaries
        """
        try:
            self.navigate_to_post(post_url)
            
            # Load more comments if needed
            self.load_more_comments(max_comments)
            
            # Use the selector you specified
            comment_selector = "//span[contains(@class, 'x1lliihq')]"
            
            comment_elements = []
            try:
                comment_elements = self.driver.find_elements(By.XPATH, comment_selector)
                self.logger.info(f"Found {len(comment_elements)} potential comment elements")
            except Exception as e:
                self.logger.error(f"Failed to find comment elements: {str(e)}")
                return []
            
            if not comment_elements:
                self.logger.warning("No comment elements found")
                return []
            
            # Filter out non-comment texts
            ui_elements = {
                "reply", "see translation", "translate", "view replies", 
                "view all replies", "hide replies", "like", "liked",
                "show more", "show less", "view more comments",
                "load more comments", "heart", "follow", "following",
                "ago", "min", "hour", "day", "week", "month", "year",
                "h", "m", "d", "w", "y"  # Time abbreviations
            }
            
            comments = []
            
            for i, comment_element in enumerate(comment_elements):
                try:
                    # Extract comment text directly from the span element
                    comment_text = comment_element.text.strip()
                    
                    # Skip if text is empty or too short
                    if not comment_text or len(comment_text) <= 2:
                        self.logger.debug(f"Skipped element {i+1}: too short or empty")
                        continue
                    
                    # Convert to lowercase for checking
                    comment_lower = comment_text.lower()
                    
                    # Skip UI elements and common non-comment text patterns
                    if comment_lower in ui_elements:
                        self.logger.debug(f"Skipped UI element {i+1}: '{comment_text}'")
                        continue
                    
                    # Skip single words that are likely UI elements
                    if len(comment_text.split()) == 1 and len(comment_text) < 10:
                        self.logger.debug(f"Skipped single word {i+1}: '{comment_text}'")
                        continue
                    
                    # Skip if it's just a time indicator (like "2h", "3 days ago", etc.)
                    if any(time_word in comment_lower for time_word in ["ago", "hour", "min", "day", "week", "month", "year"]):
                        if len(comment_text.split()) <= 3:  # Short time phrases
                            self.logger.debug(f"Skipped time indicator {i+1}: '{comment_text}'")
                            continue
                    
                    # Skip if it matches common button patterns
                    if comment_lower.startswith(("view", "show", "hide", "load", "see")):
                        if len(comment_text.split()) <= 4:  # Short UI commands
                            self.logger.debug(f"Skipped UI command {i+1}: '{comment_text}'")
                            continue
                    
                    # If we've reached max_comments, stop
                    if len(comments) >= max_comments:
                        break
                    
                    # This looks like a real comment - add it
                    comment_data = {
                        "comment": comment_text,
                        "raw_html": comment_element.get_attribute("outerHTML")
                    }
                    
                    comments.append(comment_data)
                    self.logger.debug(f"Extracted comment {len(comments)}: {comment_text[:50]}...")
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting element {i+1}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(comments)} actual comments (filtered out UI elements)")
            return comments
            
        except Exception as e:
            self.logger.error(f"Error scraping comments: {str(e)}")
            raise
    
    def save_comments_to_json(self, comments, filename="instagram_comments.json"):
        """
        Save comments to a JSON file
        
        Args:
            comments (list): List of comment dictionaries
            filename (str): Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Comments saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving comments to file: {str(e)}")
    
    def print_comment_safely(self, comment, index):
        """
        Safely print comment data handling Unicode characters
        
        Args:
            comment (dict): Comment data
            index (int): Comment index
        """
        try:
            print(f"\n--- Comment {index} ---")
            
            # Handle Unicode characters in comment text
            comment_text = comment.get('comment', '')
            try:
                print(f"Comment: {comment_text}")
            except UnicodeEncodeError:
                # Fallback: encode to ASCII with replacement characters
                safe_text = comment_text.encode('ascii', 'replace').decode('ascii')
                print(f"Comment: {safe_text}")
                print(f"Comment (raw): {repr(comment_text)}")
            
            # Optionally show first 200 chars of raw HTML for debugging
            raw_html = comment.get('raw_html', '')
            if raw_html:
                print(f"Raw HTML (first 200 chars): {raw_html[:200]}...")
            
        except Exception as e:
            print(f"Error printing comment {index}: {str(e)}")
            print(f"Comment data: {repr(comment)}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()
        self.logger.info("Browser closed")

def main(username, password, url):
    """Example usage of the Instagram Comment Scraper"""
    scraper = InstagramCommentScraper(headless=False)  # Set to True for headless mode
    comments = []  # Initialize comments list
    
    try:
        # Login credentials
        USERNAME = username
        PASSWORD = password
        POST_URL = url
        
        # Login to Instagram
        scraper.login(USERNAME, PASSWORD)
        
        # Scrape comments
        comments = scraper.scrape_comments(POST_URL, max_comments=50)
        
        # Save to JSON file first (most important - this handles Unicode perfectly)
        scraper.save_comments_to_json(comments)
        print(f"\nSuccessfully saved {len(comments)} comments to instagram_comments.json!")
        
        # Create a summary report
        print(f"\n=== SCRAPING SUMMARY ===")
        print(f"Total comments scraped: {len(comments)}")
        
        # Show character encoding info
        unicode_comments = [c for c in comments if any(ord(char) > 127 for char in c.get('comment', ''))]
        print(f"Comments with Unicode/emoji characters: {len(unicode_comments)}")
        
        return comments
        
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
        
        # Emergency save - try to save any comments that were collected before the error
        if comments:
            try:
                scraper.save_comments_to_json(comments, "emergency_save_comments.json")
                print(f"Emergency save completed: {len(comments)} comments saved to emergency_save_comments.json")
            except Exception as save_error:
                print(f"Emergency save also failed: {str(save_error)}")
        
        return comments  # Return whatever we managed to collect
        
    finally:
        # Ensure browser closes even if there are errors
        try:
            scraper.close()
        except Exception as close_error:
            print(f"Warning: Error closing browser: {str(close_error)}")

# Example usage (uncomment to test):
# if __name__ == "__main__":
#     # Replace with your actual credentials and post URL
#     username = "your_username"
#     password = "your_password"
#     post_url = "https://www.instagram.com/p/DOWPwzsjJBy/"
    
#     results = main(username, password, post_url)
#     print(f"\nFunction returned {len(results)} comments")