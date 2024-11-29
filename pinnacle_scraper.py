from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


options = Options()
options.headless = False  
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def get_player_stats_and_odds(url):
    driver.get(url)
    try:
        wait = WebDriverWait(driver, 20)
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-test-id="Collapse"]')))
        
        player_stats_and_odds = []
        for item in elements:
            try:
                title_element = item.find_element(By.CSS_SELECTOR, 'span[class*="style_title"]')
                title = title_element.text.strip()
                print(f"Found title: {title}")  

                
                if 'collapsed' in item.get_attribute('class'):
                    title_element.click()
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.style_button-wrapper__2u2GV')))


                if '(' in title and ')' in title:
                    print("In player stats section") 
                  
                    button_wrappers = item.find_elements(By.CSS_SELECTOR, 'div.style_button-wrapper__2u2GV')
                    if not button_wrappers:
                        print(f"No button wrappers found for {title}")
                    
                    odds = []
                    for wrapper in button_wrappers:
                        buttons = wrapper.find_elements(By.TAG_NAME, 'button')
                        if not buttons:
                            print(f"No buttons found in wrapper for {title}")
                        for button in buttons:
                            odd_text = button.text.strip().replace('\n', ' ')
                            print(f"Found odd: {odd_text}")  
                            odds.append(odd_text)

                    if odds:
                        player_stats_and_odds.append((title, odds))
                        print(f"Odds for {title}: {odds}")  
            except Exception as e:
                print(f"Error processing item: {e}")
        
        return player_stats_and_odds
    except Exception as e:
        print(f"An error occurred: {e}")
        driver.quit()  #
        raise4
    finally:
        driver.quit()


url = 'https://www.pinnacle.bet/en/basketball/nba/denver-nuggets-vs-minnesota-timberwolves/1591560922/#player-props'
try:
    player_stats_and_odds = get_player_stats_and_odds(url)
    for stat, odds in player_stats_and_odds:
        print(f"{stat}: {odds}")
except Exception as e:
    print(f"Scraping failed: {e}")
