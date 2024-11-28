import os
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Function to set up Selenium with ChromeDriver
def setup_driver():
    options = Options()
    options.headless = False  # Set to True for headless mode after debugging
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# Function to get game links from Pinnacle NBA matchups page
def get_game_links(driver):
    url = 'https://www.pinnacle.com/en/basketball/nba/matchups/#period:0'
    driver.get(url)
    try:
        wait = WebDriverWait(driver, 20)
        # Adjusting the CSS selector to match the game link elements
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.style_rowEnd__2vp0q > a')))
        
        game_links = [element.get_attribute('href') + '#player-props' for element in elements]
        print(f"Found {len(game_links)} game links: {game_links}")
        return game_links
    except Exception as e:
        print(f"An error occurred while getting game links: {e}")
        raise

# Function to get player stats and odds from Pinnacle
def get_pinnacle_data(driver, url):
    driver.get(url)
    try:
        wait = WebDriverWait(driver, 20)
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-test-id="Collapse"]')))
        
        pinnacle_data = []
        for item in elements:
            try:
                title_element = item.find_element(By.CSS_SELECTOR, 'span[class*="style_title"]')
                title = title_element.text.strip()
                print(f"Found title: {title}")  # Debug print

                # Click to expand the section if it is collapsed
                if 'collapsed' in item.get_attribute('class'):
                    title_element.click()
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.style_button-wrapper__2u2GV')))

                if '(' in title and ')' in title:
                    player_name, stat_type = title.split('(', 1)
                    player_name = player_name.strip()
                    stat_type = stat_type.split(')')[0].strip()

                    print(f"In player stats section: {player_name} ({stat_type})")  # Debug print
                    button_wrappers = item.find_elements(By.CSS_SELECTOR, 'div.style_button-wrapper__2u2GV')

                    odds = []
                    for wrapper in button_wrappers:
                        buttons = wrapper.find_elements(By.TAG_NAME, 'button')
                        for button in buttons:
                            odd_text = button.text.strip().replace('\n', ' ')
                            print(f"Found odd: {odd_text}")  # Debug print
                            odds.append(odd_text)

                    if odds:
                        pinnacle_line = odds[0].split(' ')[1]  # Extract line score from the first "Over" entry
                        over_decimal = odds[0].split(' ')[-1]  # Extract only the decimal value for "Over"
                        under_decimal = odds[1].split(' ')[-1]  # Extract only the decimal value for "Under"
                        pinnacle_data.append({
                            "Player Name": player_name,
                            "Stat Type": stat_type,
                            "Pinnacle Line": pinnacle_line,
                            "Over": over_decimal,
                            "Under": under_decimal
                        })
                        print(f"Odds for {title}: {odds}")  # Debug print
            except Exception as e:
                print(f"Error processing item: {e}")

        return pinnacle_data
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# Function to get player stats and odds from PrizePicks API
def get_prizepicks_data():
    url = 'https://partner-api.prizepicks.com/projections?league_id=7&per_page=10'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        projections = data['data']
        included = {item['id']: item['attributes']['display_name'] for item in data['included'] if item['type'] == 'new_player'}
        stat_types = {item['id']: item['attributes']['name'] for item in data['included'] if item['type'] == 'stat_type'}

        prizepicks_data = []
        for projection in projections:
            if projection['attributes']['odds_type'] == 'standard':  # Filter out demons and goblins
                player_id = projection['relationships']['new_player']['data']['id']
                stat_type_id = projection['relationships']['stat_type']['data']['id']
                player_name = included[player_id]
                stat_type = stat_types[stat_type_id]
                line_score = projection['attributes']['line_score']
                prizepicks_data.append({"Player Name": player_name, "Stat Type": stat_type, "Line Score": line_score})

        return prizepicks_data
    else:
        print("Failed to retrieve data")
        return []

# Get game links
driver = setup_driver()
try:
    pinnacle_urls = get_game_links(driver)
finally:
    driver.quit()

# Get data from all Pinnacle URLs
all_pinnacle_data = []
driver = setup_driver()
try:
    for url in pinnacle_urls:
        print(f"Scraping data from: {url}")
        pinnacle_data = get_pinnacle_data(driver, url)
        all_pinnacle_data.extend(pinnacle_data)
finally:
    driver.quit()

# Get data from PrizePicks API
prizepicks_data = get_prizepicks_data()

# Combine data
stat_mapping = {
    "3 Point FG": "3-PT Made",
    "Assists": "Assists",
    "Points": "Points",
    "Pts+Rebs+Asts": "Pts+Rebs+Asts",
    "Rebounds": "Rebounds"
}

combined_data = []

for pp_data in prizepicks_data:
    player_name = pp_data['Player Name']
    stat_type = stat_mapping.get(pp_data['Stat Type'], pp_data['Stat Type'])
    prizepicks_line = pp_data['Line Score']
    
    pinnacle_entry = next((item for item in all_pinnacle_data if item['Player Name'] == player_name and item['Stat Type'] == stat_type), None)
    
    if pinnacle_entry:
        pinnacle_line = pinnacle_entry['Pinnacle Line']
        pinnacle_over = pinnacle_entry['Over']
        pinnacle_under = pinnacle_entry['Under']
    else:
        pinnacle_line = pinnacle_over = pinnacle_under = None
    
    combined_data.append({
        "Player Name": player_name,
        "Stat Type": stat_type,
        "PrizePicks Line": prizepicks_line,
        "Pinnacle Line": pinnacle_line,
        "Pinnacle Over": pinnacle_over,
        "Pinnacle Under": pinnacle_under
    })

# Print combined data for debugging
for data in combined_data:
    print(data)

combined_df = pd.DataFrame(combined_data)

# Create a pivot table-like format
pivot_table = combined_df.pivot_table(index=["Stat Type", "Player Name"], values=["PrizePicks Line", "Pinnacle Line", "Pinnacle Over", "Pinnacle Under"], aggfunc='first')
pivot_table = pivot_table.reset_index()

# Check if file exists and delete it
output_file = "sports_book_comparison.xlsx"
if os.path.exists(output_file):
    os.remove(output_file)

# Write to Excel
pivot_table.to_excel(output_file, index=False)

print(f"Data written to {output_file}")