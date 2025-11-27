
from .auth_get_code import get_2fa_code 
import datetime as dt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import json
import password
import datetime
import time

def get_code(request_time = dt.datetime.now(dt.timezone.utc)):
    code = get_2fa_code(request_time)
    print(code)
    return code
   

def is_element_present(driver, by, value, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        return True
    except TimeoutException:
        return False
    
def password_page(link, driver: webdriver.Chrome, path_cookies):
    driver.get(link)
    
    try:
        with open(path_cookies, "r") as file:
            cookies = json.load(file)
        
            for cookie in cookies:
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                driver.add_cookie(cookie)
    except Exception as ex:
        print(ex)
    
    driver.refresh()

    if is_element_present(driver, By.ID, "loginform-password"):
        driver.get(link)
        email_input = driver.find_element(by=By.ID, value="loginform-username")
        email_input.clear()
        email_input.send_keys(password.login_alfa)
        password_input = driver.find_element(by=By.ID, value="loginform-password")
        password_input.clear()
        password_input.send_keys(password.passowrd_alfa)
        password_input.send_keys(Keys.ENTER)
        code = get_code(datetime.datetime.now(datetime.timezone.utc))
        code_input = driver.find_element(by=By.ID, value='login2faform-code')
        code_input.clear()
        code_input.send_keys(code)
        code_input.send_keys(Keys.ENTER)
        time.sleep(10)
        cookies = driver.get_cookies()
        with open(path_cookies, "w") as file:
            json.dump(cookies, file)
        
    return driver
