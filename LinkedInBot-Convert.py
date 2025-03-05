
import os
import random
import time
import csv
import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from bs4 import BeautifulSoup
from configure import *  # Importing configurations from configure.py

# Global Variables
SESSION_CONNECTION_COUNT = 0
TEMP_NAME = ""
TEMP_JOB = ""
TEMP_JOBMATCH = ""
TEMP_LOCATION = ""
TEMP_LOCATIONMATCH = ""
TEMP_PROFILE = []
CONNECTED = False
TIME = str(datetime.datetime.now().time())
CSV_DATA = [["Name", "Title", "Title Match", "Location", "Location Match", "Current Company", "Connected"]]

EMAIL = CONFIGURED_EMAIL
PASSWORD = CONFIGURED_PASSWORD

def launch():
    """
    Launch the LinkedIn bot.
    """
    if not os.path.isfile('visitedUsers.txt'):
        open('visitedUsers.txt', 'w').close()
    start_browser()

def start_browser():
    """
    Launches the browser based on user selection.
    """
    options = ChromeOptions() if BROWSER.upper() == "CHROME" else FirefoxOptions()
    if HEADLESS:
        options.headless = True
    
    browser = webdriver.Chrome(options=options) if BROWSER.upper() == "CHROME" else webdriver.Firefox(options=options)
    
    print("-> Launching Browser")
    browser.get('https://linkedin.com/uas/login')
    
    # Sign in
    try:
        email_element = browser.find_element(By.ID, 'username')
        email_element.send_keys(EMAIL)
        pass_element = browser.find_element(By.ID, 'password')
        pass_element.send_keys(PASSWORD)
        pass_element.submit()
        
        time.sleep(3)
        if "error" in browser.page_source:
            print("!!! Error! Verify username and password.")
            browser.quit()
            return
        print("!!! Sign-in Success!")
        linkedin_bot(browser)
    except Exception as e:
        print("Error logging in:", e)
        browser.quit()

def linkedin_bot(browser):
    """
    Runs the LinkedIn automation bot.
    """
    global SESSION_CONNECTION_COUNT, CONNECTED
    profiles_queued = []
    
    while True:
        navigate_to_network(browser)
        soup = BeautifulSoup(browser.page_source, "html.parser")
        profiles_queued = list(set(get_new_profile_urls(soup, profiles_queued)))
        
        while profiles_queued:
            if SESSION_CONNECTION_COUNT >= CONNECTION_LIMIT:
                print("Max connections reached. Stopping program.")
                return
            
            CONNECTED = False
            random.shuffle(profiles_queued)
            profile_id = profiles_queued.pop()
            browser.get(f'https://www.linkedin.com{profile_id}')
            
            TEMP_NAME = re.sub(r'\(.*?\)', '', browser.title.replace(' | LinkedIn', ''))
            TEMP_JOB = job_match(browser)
            TEMP_LOCATION = location_match(browser)
            company = "n/a"
            
            if CONNECT_WITH_USERS:
                connect_with_user(browser)
                
            TEMP_PROFILE = [TEMP_NAME, TEMP_JOB, TEMP_JOBMATCH, TEMP_LOCATION, TEMP_LOCATIONMATCH, company, CONNECTED]
            if SAVECSV:
                add_to_csv(TEMP_PROFILE, TIME)
            
            with open('visitedUsers.txt', 'a') as file:
                file.write(f'{profile_id}\n')
            
            time.sleep(random.uniform(5, 7))

def navigate_to_network(browser):
    """
    Navigates to the 'My Network' page and loads profiles.
    """
    browser.get('https://www.linkedin.com/mynetwork/')
    for _ in range(LAZY_LOAD_NUM):
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)

def connect_with_user(browser):
    """
    Sends a connection request to the user.
    """
    global SESSION_CONNECTION_COUNT, CONNECTED
    try:
        browser.find_element(By.XPATH, '//button[contains(@class, "connect")]').click()
        time.sleep(3)
        browser.find_element(By.XPATH, '//button[contains(@class, "artdeco-button")]').click()
        CONNECTED = True
        SESSION_CONNECTION_COUNT += 1
        print(f'Sent connection request. Count = {SESSION_CONNECTION_COUNT}')
    except Exception as e:
        print(f'Error connecting to {TEMP_NAME}:', e)

def get_new_profile_urls(soup, profiles_queued):
    """
    Extracts new profile URLs from the 'My Network' page.
    """
    visited_users = set(open('visitedUsers.txt').read().splitlines())
    profile_urls = []
    for a in soup.find_all('a', class_='discover-person-card__link'):
        url = a['href']
        if url not in visited_users and "/in/" in url and "connections" not in url:
            profile_urls.append(url)
    return list(set(profile_urls))

def location_match(browser):
    """
    Extracts location from profile.
    """
    soup = BeautifulSoup(browser.page_source, "html.parser")
    location_element = soup.select_one(".pv-top-card-v3--list li")
    return location_element.text.strip() if location_element else "Unknown"

def job_match(browser):
    """
    Extracts job title from profile.
    """
    soup = BeautifulSoup(browser.page_source, "html.parser")
    job_element = soup.select_one(".pv-top-card-v3--list h2")
    return job_element.text.strip() if job_element else "Unknown"

def add_to_csv(data, time):
    """
    Appends data to CSV.
    """
    filename = f'LinkedIn-{time}.csv'
    with open(os.path.join('CSV', filename), 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)

if __name__ == '__main__':
    try:
        launch()
    except Exception as e:
        print("Program Stopped Running: ", e)
