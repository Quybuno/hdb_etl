import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_dashboard_perfect():
    os.makedirs("docs/screenshots", exist_ok=True)
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1600,1200")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        pages = [
            ("http://localhost:8501", "home_overview.png"),
            ("http://localhost:8501/Duong_cong_thue", "lease_curve.png"),
            ("http://localhost:8501/So_sanh_khu", "town_comparison.png"),
            ("http://localhost:8501/Gia_dieu_chinh", "price_index.png"),
            ("http://localhost:8501/Cong_cu_tim_khu", "budget_search.png"),
            ("http://localhost:8501/Van_hanh", "operations_quality.png")
        ]

        for url, fname in pages:
            print(f"Navigating to {url}...")
            driver.get(url)
            # Wait until main content is present
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "stMain"))
            )
            time.sleep(5) # Wait for Plotly and data to fully render
            out_path = os.path.join("docs", "screenshots", fname)
            driver.save_screenshot(out_path)
            print(f"Saved: {out_path} ({os.path.getsize(out_path)} bytes)")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_dashboard_perfect()
