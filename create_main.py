from seleniumbase import SB
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from create_motivation_letter import get_llm_response
import os
from utils.logging import logger

def login(email, password, driver, sb):
    sb.wait_for_element_visible('name=username', timeout=10)
    input_email = driver.find_element(By.NAME, 'username')
    input_email.clear()
    input_email.send_keys(email)
    sb.sleep(1)

    sb.wait_for_element_visible('name=password', timeout=10)
    input_password = driver.find_element(By.NAME, 'password')
    input_password.clear()
    input_password.send_keys(password) 

    input_password.send_keys(Keys.ENTER)

def post_chercher(poste, driver):

    textarea = driver.find_element('id', 'keywords')
    textarea.clear()
    textarea.send_keys(poste)
    textarea.send_keys(Keys.ENTER)

def display_all_offers(driver):
    c = True
    while c==True:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            attachment_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//button[@class="load-more btn btn__nextpage"]')))
            attachment_button.click()
        except Exception:
            c = False

def get_offers(driver):

    display_all_offers(driver)

    page_content = driver.page_source
    soup = BeautifulSoup(page_content, 'html.parser')
    content_header = soup.find('div', class_='search-results col-xs-12 col-sm-9')

    job_links = []
    for article in content_header.find_all('article', class_='media well listing-item listing-item__jobs'):
        link_tag = article.find('a', class_='link')
        if link_tag:
            job_links.append(link_tag['href'])

    return job_links

def get_offer_details(offer_link, driver, sb):

    sb.open(offer_link)

    page_content = driver.page_source
    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Extract job description
    description_element = soup.find('h3', class_='details-body__title', text="Description de l'emploi")
    job_description = description_element.find_next('div', class_='details-body__content').get_text(separator=' ', strip=True)

    # Extract job requirements
    job_requirements = ""
    try:
        exigences_element = soup.find('h3', class_='details-body__title', text="Exigences de l'emploi")
        job_requirements = exigences_element.find_next('div', class_='details-body__content').get_text(separator=' ', strip=True)
    except Exception:
        logger.warn("something wrong !!")

    # company name
    li_element = soup.find('li', class_='listing-item__info--item listing-item__info--item-company')
    company_name = li_element.get_text(strip=True)

    li_element2 = soup.find('h1', class_='details-header__title')
    post_name = li_element2.get_text(strip=True)


    informations_offre = f""" 
            Post title : {post_name}
            Job description : {job_description}
            job requirements : {job_requirements} """

    return informations_offre, post_name, company_name

def Postuler(pdf_path, name, email, lettre_motiv, driver, sb):

    # click sur postuler
    attachment_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//button[@class="btn btn-apply btn-primary btn-lg btn-block"]')))
    attachment_button.click()
    sb.wait(1)

    #name & prenom & lettre
    page_content = driver.page_source
    soup = BeautifulSoup(page_content, 'html.parser')

    input_name = driver.find_element('name', 'name')
    input_name.clear()
    input_name.send_keys(name)
    sb.wait(1)

    input_email = driver.find_element('name', 'email')
    input_email.clear()
    input_email.send_keys(email)

    input_lettre_mot = driver.find_element('name', 'comments')
    input_lettre_mot.clear()
    input_lettre_mot.send_keys(lettre_motiv)
    sb.wait(1)

    file_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]')))
    pdf_path = "C:/Users/mhamed.bougerra/Desktop/scraping/CVs/CV.pdf"
    file_input.send_keys(os.path.abspath(pdf_path))
    sb.wait(1)

    click_to_post = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//input[@class="btn__submit-modal btn btn__orange btn__bold"]')))
    click_to_post.click()


def main(EMAIL, PASSWORD, NAME, ADRESSE, PHONE, today_date, LANGUE, pdf_path, poste):
    with SB(uc=True, test=True, locale_code="en", headless=True) as sb:
        url = "https://www.tanitjobs.com/login/"
        sb.open(url)
        sb.wait(2)
        sb.open(url)
        driver = sb.driver 
        sb.wait(7)

        try:
            login(EMAIL, PASSWORD, driver, sb)
            logger.info("Login success")
        except Exception:
            logger.error("Login failed")
            return "login failed"

        sb.wait(2)
        sb.open("https://www.tanitjobs.com")

        post_chercher(poste, driver)
        logger.info("Search for postes")
        sb.wait(1)

        offers_links = get_offers(driver)

        # for offer_link in offers_links:
        logger.info(f"Offer link: {offers_links[12]}")
        informations_offre, post_name, company_name = get_offer_details(offers_links[12], driver, sb)
        logger.info("Get offers détails")
        motivation_lettre= get_llm_response(informations_offre, EMAIL, NAME, ADRESSE, PHONE, today_date, LANGUE)
        logger.info("Lettre de motivation has been created successfully")
        Postuler(pdf_path, NAME, EMAIL, motivation_lettre, driver, sb)
        logger.info("Motivation lettre: {}".format(motivation_lettre))
        logger.info("Your candidature has been envoyée with success")
        sb.wait(20)
