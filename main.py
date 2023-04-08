import csv
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import phonenumbers

# Funzione per separare il prefisso dal numero di telefono
def separate_prefix(number, prefix_length=3):
    return number[:prefix_length] + " " + number[prefix_length:]


# Funzione per convertire un numero di telefono nel formato E.164
def convert_to_e164(phone_number, default_region='IT'):
    try:
        parsed_number = phonenumbers.parse(phone_number, default_region)
        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return None


def split_phone_numbers(row):
    phone_numbers = re.split(r'\s{2,}', row['Telefono'])
    new_rows = []
    for phone_number in phone_numbers:
        new_row = row.copy()
        new_row['Telefono'] = phone_number
        new_rows.append(new_row)
    return new_rows


key_search = input('inserisci il settore: ')
key_provincia_search = input('inserisci provincia: ')
# create Firefox driver with options and set to automatically accept cookies
options = webdriver.FirefoxOptions()
options.set_preference("network.cookie.cookieBehavior", 0)
driver = webdriver.Firefox(options=options)

# navigate to website and accept cookies
driver.get("https://www.paginegialle.it/")
accept_button = driver.find_element(By.XPATH, "/html/body/div[3]/div/div/div/div[2]/button[3]")
if accept_button:
    accept_button.click()

# enter search keyword and submit search
driver.find_element(By.CSS_SELECTOR, "#cosa").send_keys(key_search)
BUTTONX = driver.find_element(By.XPATH, "/html/body/main/div/section[1]/div/div/div[1]/div/div/div/div[5]/a[2]")
BUTTONX.click()
driver.find_element(By.CSS_SELECTOR, '#dove').send_keys(key_provincia_search + Keys.ENTER)
# wait for search results to load and accept cookies if necessary
time.sleep(5)

# click on "Load more" button until there are no more results
while True:
    try:
        load_more_button = driver.find_element(By.XPATH, "/html/body/main/div/div[2]/div[1]/div[3]/div[2]/a")
        load_more_button.click()
        time.sleep(5)
    except:
        break

# get the HTML of the current page
html = driver.page_source

# parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find all the elements with class 'search-itm'
search_itms = soup.find_all('div', {'class': 'search-itm'})
info_list = soup.find_all('div', {'class': 'search-itm'})
elements = driver.find_elements(By.CLASS_NAME, "search-itm")
# Iterate over each 'search-itm' element and print the desired information
# create empty lists to store data
companies = []
addresses = []
telephones = []
# add new empty lists for the new columns
ids = []
names = []
surnames = []

for i, search_itm in enumerate(search_itms):

    try:
        telefono_list = info_list[i].find_all('div', {'class': 'search-itm__phone hidden'})
        telefono = ' '.join([t.get_text().strip() for t in telefono_list])

    except:
        telefono = ""
    try:
        address_element = elements[i].find_element(By.CLASS_NAME, f"search-itm__adr")
        address_text = address_element.text
    except:
        address_text = ""

    try:
        company_element = elements[i].find_element(By.CLASS_NAME, f"search-itm__rag")
        company_text = company_element.text
    except:
        company_text = ""

    # add a unique ID for each record
    ids.append(i)
    # add constant values for "nome" and "cognome" columns
    names.append("nome")
    surnames.append("cognome")

    companies.append(company_text)
    addresses.append(address_text)
    telephones.append(telefono)

# add new columns to the data dictionary
data = {'ID': ids, 'Azienda': companies, 'Indirizzo': addresses, 'Telefono': telephones, 'Nome': names,
        'Cognome': surnames}

# create DataFrame from the data dictionary
df = pd.DataFrame(data)
# Dividi le righe con più numeri di telefono
expanded_rows = []
for _, row in df.iterrows():
    expanded_rows.extend(split_phone_numbers(row))
expanded_df = pd.DataFrame(expanded_rows)
expanded_df['Telefono'] = expanded_df['Telefono'].apply(convert_to_e164)
expanded_df['ID'] = range(1, len(expanded_df) + 1)

# Elimina l'ultima riga
expanded_df = expanded_df.iloc[:-1]
expanded_df.reset_index(drop=True, inplace=True)
expanded_df.to_csv('prova.csv', index=False)

# close the driver
driver.quit()
