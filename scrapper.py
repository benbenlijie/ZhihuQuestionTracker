from selenium import webdriver
from selenium.webdriver.firefox import service
from selenium.webdriver.common.by import By
import time
import datetime




class ZhihuScraper:
    POTENTIAL_URL = 'https://www.zhihu.com/creator/potential-question/potential/100002/all'
    
    def __init__(self, driver_path='driver/geckodriver', cookie_path='cookies'):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')

        self.driver = webdriver.Firefox(
            options=options,
            service=webdriver.FirefoxService(executable_path=driver_path)
        )
        self.cookie_path = cookie_path
    
    def load_cookies(self):
        with open(self.cookie_path, 'r') as file:
            data = file.read().split("; ")
        for pair in data:
            iterms = pair.split("=")
            name = iterms[0]
            value = pair[len(name)+1:]
            cookie_dict = {'name': name, 'value': value}
            self.driver.add_cookie(cookie_dict)

    def fetch_data(self, url=POTENTIAL_URL):
        self.driver.get(url)
        self.load_cookies()
        self.driver.get(url)  # 重新加载页面以应用Cookies
        time.sleep(5)  # 等待页面加载
        for _ in range(10):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
        time.sleep(1.0)
        results = []
        cards = self.driver.find_elements(By.CLASS_NAME, "Card")
        for card in cards:
            list_root = card.find_element(By.XPATH, ".//*[@role='list']")
            items = list_root.find_elements(By.XPATH, "./div[contains(@class, 'vurnku')]")
            for item in items:
                question_links = item.find_elements(By.XPATH, ".//a[contains(@href, 'question')]")
                question_links = [el for el in question_links if "write" not in el.get_attribute("href")]
                
                if len(question_links) == 0:
                    continue
                
                link = question_links[0]
                question_text = link.find_element(By.XPATH, ".//div").text
                question_url = link.get_attribute('href')
                
                topic_links = item.find_elements(By.XPATH, ".//a[contains(@href, 'topic')]")
                topics = [el.text for el in topic_links]
                
                date_els = item.find_elements(By.XPATH, u".//div[contains(text(), '时间')]")
                date = date_els[0].text if len(date_els) > 0 else ""
                
                divs = item.find_elements(By.XPATH, "./div/div")
                potential_score_raw = divs[1].text # '7.9 分'
                view_amount_raw = divs[2].text # '16.7 万\n共 32.9 万'
                answer_amount_raw = divs[3].text # '61\n共 61'
                
                data = {
                    "question_text": question_text,
                    "question_url": question_url,
                    "topics": topics,
                    "date_raw": date,
                    "potential_score_raw": potential_score_raw,
                    "view_amount_raw": view_amount_raw,
                    "answer_amount_raw": answer_amount_raw
                }
                data.update(self._extract_information(
                    **data
                ))
                results.append(data)
        return results

    def close(self):
        self.driver.quit()
        
    def _extract_information(self, 
                             date_raw,
                             potential_score_raw, 
                             view_amount_raw, 
                             answer_amount_raw, 
                             **kwargs):
        date_parts = date_raw.split("：")
        if len(date_parts) > 1:
            date = date_parts[1]
        else:
            date = None
        # 提取评分
        potential_score = float(potential_score_raw.split()[0])
        
        # 提取观看量增量和总量
        view_amount_parts = view_amount_raw.split('\n')
        view_increment_raw, view_total_raw = view_amount_parts[0], view_amount_parts[1]
        
        # 处理增量，检查是否包含'万'这个字符
        view_increment = float(view_increment_raw.split()[0]) * 10000 if '万' in view_increment_raw else float(view_increment_raw.split()[0])
        
        # 处理总量，检查是否包含'万'这个字符
        view_total = float(view_total_raw.split()[1]) * 10000 if '万' in view_total_raw else float(view_total_raw.split()[1])
        
        
        # 提取回答量增量和总量
        answer_amount_parts = answer_amount_raw.split('\n')
        answer_increment = int(answer_amount_parts[0])
        answer_total = int(answer_amount_parts[1].split()[1])
        
        return {
            "potential_score": potential_score,
            "view_increment": int(view_increment),
            "view_total": int(view_total),
            "answer_increment": answer_increment,
            "answer_total": answer_total,
            "date": date,
        }

if __name__ == "__main__":
    # 使用示例
    scraper = ZhihuScraper()
    data = scraper.fetch_data()
    scraper.close()

    import json
    with open("potential_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    for item in data:
        print(item)
