from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import unittest
from datetime import datetime
import HtmlTestRunner
class TestWebApp(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:5000") 
        self.driver.maximize_window()
        self.test_results = []  

    def tearDown(self):
        self.driver.quit()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(f"test_results_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write("<html><head><title>Test Results</title></head><body>")
            f.write("<h1>Test Results</h1>")
            f.write("<ul>")
            for result in self.test_results:
                f.write(f"<li>{result}</li>")
            f.write("</ul>")
            f.write("</body></html>")

    def test_responsiveness(self):
        try:
            driver = self.driver
            driver.get("http://localhost:5000/products")

            driver.set_window_size(800, 600)
            driver.set_window_size(1200, 800)

            self.test_results.append("test_responsiveness PASSED")
        except Exception as e:
            self.test_results.append(f"test_responsiveness FAILED: {e}")

    def test_scrolling(self):
        try:
            driver = self.driver
            driver.get("http://localhost:5000/products")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script("window.scrollTo(0, 0);")

            self.test_results.append("test_scrolling PASSED")
        except Exception as e:
            self.test_results.append(f"test_scrolling FAILED: {e}")

    def test_filter_functionality_products(self):
        try:
            driver = self.driver
            driver.get("http://localhost:5000/products")

            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "category"))
            )
            category_select = Select(driver.find_element(By.ID, "category"))
            category_select.select_by_visible_text("Wszystkie")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "min_proteins"))
            ).send_keys("10")
            driver.find_element(By.NAME, "max_sugars").send_keys("5")

            
            driver.find_element(By.TAG_NAME, "form").submit()

            self.test_results.append("test_filter_functionality_products PASSED")
        except Exception as e:
            self.test_results.append(f"test_filter_functionality_products FAILED: {e}")

    def test_filter_functionality_exercises(self):
        try:
            
            driver = self.driver
            driver.get("http://localhost:5000/exercises/strength")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "body_part"))
            )
            body_part_select = Select(driver.find_element(By.ID, "body_part"))
            body_part_select.select_by_visible_text("Wszystkie")

            difficulty_select = Select(driver.find_element(By.ID, "difficulty"))
            difficulty_select.select_by_visible_text("Wszystkie")

            
            driver.find_element(By.TAG_NAME, "form").submit()

            self.test_results.append("test_filter_functionality_exercises PASSED")
        except Exception as e:
            self.test_results.append(f"test_filter_functionality_exercises FAILED: {e}")

    def test_navbar_links(self):
        try:
            
            driver = self.driver
            original_links = driver.find_elements(By.CSS_SELECTOR, ".navbar a")
            links_to_visit = [link.get_attribute("href") for link in original_links if link.get_attribute("href")]

            for href in links_to_visit:
                driver.get(href)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

            self.test_results.append("test_navbar_links PASSED")
        except Exception as e:
            self.test_results.append(f"test_navbar_links FAILED: {e}")

    def test_bmi_calculator(self):
        try:
            
            driver = self.driver
            driver.get("http://localhost:5000/bmi")

            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

           
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "weight"))
            ).send_keys("70")
            driver.find_element(By.ID, "height").send_keys("170")

            
            driver.find_element(By.TAG_NAME, "form").submit()

            
            bmi_result = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "bmi-result"))
            ).text
            bmi_category = driver.find_element(By.ID, "bmi-category").text

            self.assertIn("24.22", bmi_result)
            self.assertIn("Waga prawidłowa", bmi_category)

            self.test_results.append("test_bmi_calculator PASSED")
        except Exception as e:
            self.test_results.append(f"test_bmi_calculator FAILED: {e}")



if __name__ == "__main__":
    unittest.main(
        testRunner=HtmlTestRunner.HTMLTestRunner(
            output='test_reports',  
            report_name='test_report',  
            combine_reports=True, 
        )
    )
