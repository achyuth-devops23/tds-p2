import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from llm_helper import ask_llm

def get_driver():
    """Initialize headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_quiz_page(url):
    """Fetch and render the quiz page"""
    driver = get_driver()
    try:
        driver.get(url)
        # Wait for result div to be populated
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "result"))
        )
        time.sleep(2)  # Extra wait for JS execution
        
        page_html = driver.page_source
        result_text = driver.find_element(By.ID, "result").text
        
        return result_text, page_html
    finally:
        driver.quit()

def extract_submit_url(quiz_text, page_html, quiz_url):
    """Extract the submit URL from quiz instructions"""
    import re
    
    # Look for submit URL in text
    url_pattern = r'https?://[^\s<>"]+/submit'
    match = re.search(url_pattern, quiz_text)
    if match:
        return match.group(0)
    
    # Look in HTML
    match = re.search(url_pattern, page_html)
    if match:
        return match.group(0)
    
    # Fallback: construct from quiz URL
    return quiz_url.replace('/quiz-', '/submit')

def submit_answer(email, secret, quiz_url, answer, submit_url):
    """Submit answer to the quiz endpoint"""
    payload = {
        "email": email,
        "secret": secret,
        "url": quiz_url,
        "answer": answer
    }
    
    try:
        response = requests.post(submit_url, json=payload, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Error submitting answer: {e}")
        return None

def solve_single_quiz(email, secret, quiz_url):
    """Solve a single quiz question"""
    print(f"Fetching quiz from: {quiz_url}")
    
    try:
        quiz_text, page_html = fetch_quiz_page(quiz_url)
    except Exception as e:
        print(f"Error fetching quiz page: {e}")
        return None
    
    print(f"Quiz text:\n{quiz_text}\n")
    
    # Extract submit URL
    submit_url = extract_submit_url(quiz_text, page_html, quiz_url)
    print(f"Submit URL: {submit_url}")
    
    # Use LLM to solve the quiz
    answer = ask_llm(quiz_text, page_html)
    
    print(f"Submitting answer: {answer}")
    
    result = submit_answer(email, secret, quiz_url, answer, submit_url)
    
    if result:
        print(f"Result: {result}")
        return result
    
    return None

def solve_quiz(email, secret, initial_url):
    """Main solver that handles the quiz chain"""
    start_time = time.time()
    current_url = initial_url
    attempts = 0
    max_attempts = 20  # Prevent infinite loops
    
    while current_url and attempts < max_attempts:
        elapsed = time.time() - start_time
        if elapsed > 170:  # Stop before 3 minutes
            print("Time limit approaching, stopping...")
            break
        
        attempts += 1
        result = solve_single_quiz(email, secret, current_url)
        
        if not result:
            print("No result received, stopping...")
            break
        
        if result.get('correct'):
            print(f"✓ Correct answer!")
            next_url = result.get('url')
            if next_url:
                current_url = next_url
                time.sleep(1)  # Brief pause between questions
            else:
                print("Quiz completed!")
                break
        else:
            print(f"✗ Wrong answer: {result.get('reason')}")
            # Check if we got a next URL to skip to
            next_url = result.get('url')
            if next_url and next_url != current_url:
                print("Skipping to next question...")
                current_url = next_url
            else:
                # Could implement retry logic here
                print("No skip URL provided, stopping...")
                break
    
    print(f"Quiz solving finished. Attempts: {attempts}")
