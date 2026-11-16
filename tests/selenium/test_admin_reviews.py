"""Selenium tests of the independent admin reviews demo.
Run backend + frontend before pytest. No user account or login required.
"""
import os
import uuid
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

URL = os.getenv('REVIEWS_URL','http://localhost:5173')

@pytest.fixture(scope='function')
def driver():
    browser = webdriver.Edge()
    browser.get(URL)
    yield browser
    browser.quit()


def ready(driver):
    return WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'[data-testid="total-comments"]')))


def test_01_dashboard_loads_without_login(driver):
    ready(driver)
    assert 'Reseñas del negocio' in driver.page_source


def test_02_total_comments_statistic_is_visible(driver):
    label=ready(driver)
    assert label.text.isdigit()


def test_03_new_review_form_opens(driver):
    ready(driver)
    driver.find_element(By.CSS_SELECTOR,'[data-testid="toggle-form"]').click()
    assert driver.find_element(By.CSS_SELECTOR,'[data-testid="review-form"]').is_displayed()


def test_04_rating_filter_has_five_stars(driver):
    ready(driver)
    select=driver.find_element(By.CSS_SELECTOR,'[data-testid="filter-rating"]')
    assert any(option.get_attribute('value')=='5' for option in select.find_elements(By.TAG_NAME,'option'))


def test_05_search_shows_empty_state(driver):
    ready(driver)
    term='sin_coincidencia_' + uuid.uuid4().hex
    driver.find_element(By.CSS_SELECTOR,'[data-testid="search-review"]').send_keys(term)
    WebDriverWait(driver,5).until(EC.visibility_of_element_located((By.CSS_SELECTOR,'[data-testid="empty-reviews"]')))


def test_06_publish_and_display_date(driver):
    ready(driver)
    name='Prueba '+uuid.uuid4().hex[:7]
    driver.find_element(By.CSS_SELECTOR,'[data-testid="toggle-form"]').click()
    driver.find_element(By.CSS_SELECTOR,'[data-testid="review-user"]').send_keys(name)
    driver.find_element(By.CSS_SELECTOR,'[data-testid="review-comment"]').send_keys('Reseña de prueba automática con texto suficiente.')
    driver.find_element(By.CSS_SELECTOR,'[data-testid="submit-review"]').click()
    WebDriverWait(driver,10).until(
        lambda browser: any(name in card.text
                            for card in browser.find_elements(By.CSS_SELECTOR,'[data-testid="review-card"]'))
    )
    assert any('Publicado el' in card.text for card in driver.find_elements(By.CSS_SELECTOR,'[data-testid="review-card"]') if name in card.text)
