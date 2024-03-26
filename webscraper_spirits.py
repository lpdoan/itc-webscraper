"""
Status : 
Latest Update : Feb 2024


"""

import selenium
import requests
import time
from io import StringIO # necessary
import openpyxl 
from openpyxl import load_workbook # not necessary
import pandas as pd
import numpy as np
from selenium import webdriver # selenium for dynamic rendering request data generated with JavaScript
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select # new
from selenium.webdriver.edge.options import Options
from pathlib import Path
import json
import random
from set_query_params import set_query_params

login = pd.read_csv('input/login.txt', sep=",", header=None)
user = login.iloc[0, 0]
pw = login.iloc[0, 1]

# print("The user log in is", user, ". The password is", pw)
countries = list(pd.read_csv("input/country_list.txt"))
countries

spirits_hs_df = pd.read_excel("./input/hs_coding_coverage_2023.xlsx", sheet_name="MASTERLIST_SPIRITS_HS_CODES", converters={"hs_code": str})
spirits_hs_df = spirits_hs_df.drop("Column1", axis=1)


###### ES NERQEVI CODITIONNER@ PETQA TULACNEL
# drop rows where HS code is NaN or full product description is Trade of heading 2208, not elsewhere specified
idx_nan_1 = spirits_hs_df[(spirits_hs_df["full_product_description"] =="Commodities not elsewhere specified")].index
spirits_hs_df = spirits_hs_df.drop(idx_nan_1)

# beer description
# add description to
LIQUID_DESC = open("./input/liquid_desc.json")
liquid_desc = json.load(LIQUID_DESC)
liquid_desc # 22030001, 22030009, 22030010 are beer codes

USER_AGENTS = open("./input/user_agents.json")
user_agents = json.load(USER_AGENTS)
user_agents # dictionary with key = user_agents, value = list of user agents

### INITIALIZE A WEBDRIVER OBJECT ###
# Browser driver with randomized user agent to avoid using the same user-agent every time
rand_user_agent = random.choice(user_agents["user_agents"])
print(rand_user_agent)

downloads_path = r"C:\Users\U744320\itc-webscraper\downloads\spirits\exports"

options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"--user-agent={rand_user_agent}")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option("prefs", {
  "download.default_directory": downloads_path,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

driver = webdriver.Edge(options=options)
driver.get("https://www.bing.com/")
driver.implicitly_wait(3)

login_page = "https://idserv.marketanalysis.intracen.org/Account/Login?ReturnUrl=%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3DTradeMap%26scope%3Dopenid%2520email%2520profile%2520offline_access%2520ActivityLog%26redirect_uri%3Dhttps%253A%252F%252Fwww.trademap.org%252FLoginCallback.aspx%26state%3D8e91e1ec50d647ceb649bd87cf09c60c%26response_type%3Dcode%2520id_token%26nonce%3D0c095fc5b9404e1495028c3715432542%26response_mode%3Dform_post"
driver.get(login_page)
time.sleep(1)

# PUT SOME SLEEP TIME (1 SECOND) IN BETWEEN ACTIONS TO AVOID BEING BANNED FROM THE WEBSITE !!!
time.sleep(1)
user_element = driver.find_element(By.ID, "Username")
user_element.send_keys(user)
time.sleep(1)
pw_element = driver.find_element(By.ID, "Password")
pw_element.send_keys(pw)
time.sleep(2)

# click the login button to log in
login_button = driver.find_element(By.NAME, "button")
login_button.click()

time.sleep(30)
login_button_2 = driver.find_element(By.ID, "ctl00_MenuControl_Label_Login")
login_button_2.click()
time.sleep(1)

database_link = "https://www.trademap.org/Country_SelProductCountry_TS.aspx?nvpm=1%7c251%7c%7c%7c%7c2204%7c%7c%7c4%7c1%7c1%7c1%7c2%7c1%7c2%7c2%7c1%7c1"
driver.get(database_link)

def select_code(driver, value):
    code_list_elem=driver.find_element(By.NAME, "ctl00$NavigationControl$DropDownList_Product")
    code_select = Select(code_list_elem)
    code_select.select_by_value(value)

def select_country(driver,country_name):
    country_list= driver.find_element(By.NAME, "ctl00$NavigationControl$DropDownList_Country")
    country_select = Select(country_list)
    country_select.select_by_visible_text(country_name)

def change_tradetype(type):
    """
    define the functions to help with selecting the right trade type
    type can be "E" (for export) or "I" for import
    """
    tradetype_element = driver.find_element(By.NAME,"ctl00$NavigationControl$DropDownList_TradeType")
    tradetype_element_select = Select(tradetype_element)
    tradetype_element_select.select_by_value(type)

# try downloading import and export data for Argentina first
# argentina_hs_import = spirits_hs_df[(spirits_hs_df["reporting_country"]== "Argentina") &
#                                     (spirits_hs_df["flow"]== "import")]
# argentina_hs_export = spirits_hs_df[(spirits_hs_df["reporting_country"]== "Argentina") &
#                                     (spirits_hs_df["flow"]== "export")]

# select_country(driver, "Argentina")

# for code in argentina_hs_export["hs_code"]:
#     select_code(driver=driver, value= code)
#     time.sleep(0.25)
#     download_button = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_ImageButton_Text")
#     time.sleep(0.5)
#     download_button.click()        

# change_tradetype("E")

# for code in argentina_hs_export["hs_code"]:
#     select_code(driver=driver, value= code)
#     time.sleep(0.25)
#     download_button = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_ImageButton_Text")
#     time.sleep(0.5)
#     download_button.click()

# turn on this config if you want to download data from 2013 onwards
set_query_params(driver=driver)

# turn on this config if you only want to download last 12 months and instead of set_query params use the below query

# def query_params_last_12_months(driver):
#     # frequency
#     frequency_indicator = driver.find_element(By.NAME, "ctl00$NavigationControl$DropDownList_OutputType")
#     frequency_select = Select(frequency_indicator)
#     frequency_select.select_by_value("TSM")

#     # quantities
#     quantity_indicator = driver.find_element(By.NAME, "ctl00$NavigationControl$DropDownList_TS_Indicator")
#     quantity_select = Select(quantity_indicator)
#     quantity_select.select_by_value("Q")

#     # # starting date
#     # graph = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_Label_tabGraph")
#     # graph.click()
#     # time.sleep(3)
#     # start_date = driver.find_element(By.NAME, "ctl00$PageContent$ctl00$DDL_TimePeriod_RangeFromMQ")
#     # start_date_select = Select(start_date)
#     # start_date_select.select_by_value("01") 

#     # start_year = driver.find_element(By.NAME, "ctl00$PageContent$ctl00$DDL_TimePeriod_RangeFromY")
#     # start_year_select = Select(start_year)
#     # start_year_select.select_by_value("2013") # we need to change the input by a formula (e.g. str(current year - 10))

#     # update_button = driver.find_element(By.NAME, "ctl00$PageContent$ctl00$Button_ChartReCalc")
#     # update_button.click()

#     # # switch back to table tab
#     # table_tab = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_Label_tabTable")
#     # table_tab.click()

#     # in table view, set maximum display rows to 300
#     max_rows_option = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_DropDownList_PageSize")
#     max_rows_select = Select(max_rows_option)
#     max_rows_select.select_by_value("300")

# query_params_last_12_months(driver = driver)

###IMPORTS###

# import data
# import_spirits = spirits_hs_df[spirits_hs_df["flow"] == "import"]
# import_spirits = import_spirits[["reporting_country", "hs_code"]]
# import_spirits

# select_code(driver = driver, value = "22")
# select_code(driver = driver, value = "2208")
# select_code(driver = driver, value = "220820")

# import_spirits = import_spirits[import_spirits["reporting_country"] == "Canada"]

# colombia : potential duplicate issues
# control for duplicate rows when cleaning data later

# import_spirits[import_spirits["reporting_country"] == "Czech Republic"].reset_index().iloc[10:, :]

# for index, row in import_spirits[import_spirits["reporting_country"] == "Estonia"].reset_index(drop=True).loc[161:].iterrows():
#     select_country(driver, row["reporting_country"])    
#     select_code(driver, row["hs_code"])
#     download_button = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_ImageButton_Text")
#     download_button.click()
#     print("downloaded", row["reporting_country"], row["hs_code"])


### Exports ###

change_tradetype("E")

export_spirits = spirits_hs_df[spirits_hs_df["flow"] == "export"]
export_spirits = export_spirits[["reporting_country", "hs_code"]]
export_spirits

select_code(driver = driver, value = "22") #22= bevarage
select_code(driver = driver, value = "2208") #2208= spirits
select_code(driver = driver, value = "220820") #220820= to show the 10 digits in the drop down menu

for index, row in export_spirits[export_spirits["reporting_country"] == "Spain"].reset_index(drop=True).loc[169:].iterrows(): #.reset_index(drop=True).loc[x:].iterrows() (*x=number of files) to start loading again 
    select_country(driver, row["reporting_country"])    
    select_code(driver, row["hs_code"])
    download_button = driver.find_element(By.ID, "ctl00_PageContent_GridViewPanelControl_ImageButton_Text")
    download_button.click()
    print("downloaded", row["reporting_country"], row["hs_code"])

#### 22080000 ####

downloads_path = r"C:\Users\U744320\itc-webscraper\downloads\spirits\22080000\exports" ##\imports

set_query_params(driver=driver)

change_tradetype("E")

add_cleaned_spirits = spirits_hs_df[spirits_hs_df["hs_code"] == "22080000"]
add_cleaned_spirits = add_cleaned_spirits[["reporting_country", "flow"]]
add_cleaned_spirits

select_code(driver = driver, value = "22") #22= bevarage
select_code(driver = driver, value = "2208") #2208= spirits
select_code(driver = driver, value = "220820") #220820= to show the 10 digits in the drop down menu
select_code(driver = driver, value = "22080000")




