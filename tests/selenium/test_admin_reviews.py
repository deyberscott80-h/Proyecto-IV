"""Independent review admin UI. Runs on Edge headless, NO login needed.

Selenium prerequisites: live React on :5173; live FastAPI on :8000.
Tests are designed to work with SweetAlert2 confirmation dialogs.
"""
import os
import uuid
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = os.getenv("REVIEWS_URL", "http://127.0.0.1:5173")


@pytest.fixture
def driver(request):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,950")
    browser = webdriver.Edge(options=options)
    browser.get(URL)
    yield browser
    output = Path("reports/screenshots")
    output.mkdir(parents=True, exist_ok=True)
    browser.save_screenshot(str(output / f"{request.node.name}.png"))
    browser.quit()


def ready(driver):
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="total-comments"]'))
    )
    WebDriverWait(driver, 20).until(
        lambda d: "Cargando comentarios" not in d.page_source
    )


def confirm_if_shown(driver):
    # SweetAlert2 added to user's frontend; old versions skip this dialog.
    try:
        button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm"))
        )
        button.click()
    except Exception:
        pass


def create_review(driver, comment="Ok"):
    name = "CI-" + uuid.uuid4().hex[:8]
    driver.find_element(By.CSS_SELECTOR, '[data-testid="toggle-form"]').click()
    driver.find_element(By.CSS_SELECTOR, '[data-testid="review-user"]').send_keys(name)
    if comment:
        driver.find_element(By.CSS_SELECTOR, '[data-testid="review-comment"]').send_keys(comment)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="submit-review"]').click()
    confirm_if_shown(driver)
    cards = WebDriverWait(driver, 15).until(
        lambda d: [c for c in d.find_elements(By.CSS_SELECTOR, '[data-testid="review-card"]')
                   if name in c.text]
    )
    return name, cards[0]


def test_01_admin_dashboard_visible(driver):
    ready(driver)
    assert "Reseñas del negocio" in driver.page_source


def test_02_total_stat_shown(driver):
    ready(driver)
    label = driver.find_element(By.CSS_SELECTOR, '[data-testid="total-comments"]')
    assert label.text.isdigit()


def test_03_can_open_create_form(driver):
    ready(driver)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="toggle-form"]').click()
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="review-form"]').is_displayed()


def test_04_rating_filter_has_5_stars(driver):
    ready(driver)
    select = driver.find_element(By.CSS_SELECTOR, '[data-testid="filter-rating"]')
    values = [x.get_attribute("value") for x in select.find_elements(By.TAG_NAME, "option")]
    assert "5" in values and "1" in values


def test_05_search_empty_state(driver):
    ready(driver)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="search-review"]').send_keys(uuid.uuid4().hex)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="empty-reviews"]'))
    )


def test_06_publish_short_comment_and_date(driver):
    ready(driver)
    name, card = create_review(driver, "Ok")
    assert name in card.text
    assert "Publicado el" in card.text
    assert "Ok" in card.text


def test_07_publish_without_comment(driver):
    ready(driver)
    _, card = create_review(driver, "")
    assert "Publicado el" in card.text


def test_08_reply_to_comment(driver):
    ready(driver)
    name, card = create_review(driver, "Buen trato")
    card.find_element(By.XPATH, ".//button[normalize-space()='Responder']").click()
    card.find_element(By.TAG_NAME, "textarea").send_keys("Gracias por su reseña")
    card.find_element(By.XPATH, ".//button[normalize-space()='Guardar respuesta']").click()
    confirm_if_shown(driver)
    WebDriverWait(driver, 15).until(
        lambda d: any("Gracias por su reseña" in c.text
                      for c in d.find_elements(By.CSS_SELECTOR, '[data-testid="review-card"]')
                      if name in c.text)
    )


def test_09_delete_comment(driver):
    ready(driver)
    name, card = create_review(driver, "Para eliminar")
    card.find_element(By.XPATH, ".//button[normalize-space()='Eliminar']").click()
    confirm_if_shown(driver)
    WebDriverWait(driver, 15).until(
        lambda d: not any(name in c.text for c in d.find_elements(
            By.CSS_SELECTOR, '[data-testid="review-card"]'))
    )
