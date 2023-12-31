from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

driver_path = r"C:\DriversSel\chromedriver-win64\chromedriver.exe"

# Create a Service instance with the specified driver path
service = Service(executable_path=driver_path)

# Create ChromeOptions instance
chrome_options = Options()

# Collect the name of the writer that will be used for web scraping
print("Welcome to the program that will web-scrape all the books of your favorite writer.\n")
author = input("Please insert the name of the author: ")

# Create the Chrome webdriver instance with options and the Service instance
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window()
driver.implicitly_wait(15)
driver.get("https://lubimyczytac.pl/")

# Wait for the cookie consent button to be clickable
cookie_accept = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='onetrust-accept-btn-handler']")))

# Click the cookie consent button
cookie_accept.click()

driver.find_element(By.XPATH, "//input[@class='searchbox__input']").send_keys(author)
search_button = driver.find_element(By.XPATH, "//button[normalize-space()='Szukaj']")
search_button.send_keys(Keys.ENTER)
time.sleep(2)

# Set to store unique book titles
unique_titles = set()

df = pd.DataFrame(columns=['ID', 'Title', 'Book rating', 'Total votes'])
book_id = 1

try:
    #  Check if any books are available for the author provided
    books_available = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[@id='searchksiazki']")))

    try:
        while True:
            # Check if the pagination button is present
            pagination_button = driver.find_element(By.ID, "buttonPaginationList")

            # Click on pagination button as long as it's available
            while pagination_button.is_displayed() and pagination_button.is_enabled():

                #  Auto-scrolling down the page if pagination button is available
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                pagination_button.click()

                # Wait for the content to load
                time.sleep(3)

            # Update the page source to get the new content after clicking the button
            page_source = driver.page_source

            # Use BeautifulSoup
            soup = BeautifulSoup(page_source, 'lxml')
            books = soup.find_all('div', class_='authorAllBooks__single')

            for index, book in enumerate(books):
                titles = book.find('a').text.strip().replace('\n', '').replace('\r', '')
                rating = book.find('span', class_="listLibrary__ratingStarsNumber").text.strip().replace('\n', '').replace(
                    '\r', '')
                votes = book.find('div', class_="listLibrary__ratingAll").text.strip().split()

                # Check if the title is already printed
                if titles not in unique_titles:
                    unique_titles.add(titles)

                    print(f"{index + 1}) Book title: {titles}")
                    print(f"Book rating: {rating}/10.0")
                    print(f"Total votes: {votes[0]}")
                    print()

                    new_row = pd.DataFrame([[book_id, titles, rating + "/10.0", votes[0]]],
                                           columns=['ID', 'Title', 'Book rating', 'Total votes'])
                    df = pd.concat([df, new_row], ignore_index=True)
                    book_id += 1

            # Check if there are more pages
            next_page_button = driver.find_element(By.XPATH, "//li[@id='buttonPaginationList']//a[@rel='next']")

            if 'disabled' in next_page_button.get_attribute('class'):
                print("No more pages to load. Exiting loop.")
                break

    except NoSuchElementException:
        # If NoSuchElementException occurs, it means the pagination button is not present
        print("No pagination button found. Exiting loop.")

    finally:
        driver.quit()

except:
    #  Print a message for the user in case no books is found for the provided author
    print("No books available for the author provided. Please try again!")

# Saving data frame to csv file
df.to_csv('books2.csv', index=False)  # Path can be adjusted by the user
