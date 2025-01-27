import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
from threading import Thread
import queue
from queue import Empty

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logger_main = logging.getLogger('exception')
exp = logging.FileHandler('exception.log', mode='w', encoding='utf-8')
formatter_main = logging.Formatter(FORMAT)
exp.setFormatter(formatter_main)
logger_main.addHandler(exp)
logger_main.setLevel(logging.DEBUG)

def fulling_queue(link, queue_colors):
    """
    Заполняет очередь цветов, извлекая их из указанного URL.

    Аргументы:
    - link: URL страницы для парсинга.
    - queue_colors: Очередь для хранения ссылок на цвета.

    Возвращает:
    - Обновленную очередь цветов.
    """
    options = webdriver.ChromeOptions()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--incognito")
    options.add_argument('headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(link)
    time.sleep(5)

    colors_block = driver.find_elements(By.CSS_SELECTOR, 'a[style="border-radius:6px;"]')

    for j in colors_block:
        queue_colors.put(j.get_attribute('href'))

    return queue_colors

class Parser(Thread):
    """
    Потоковый класс для парсинга товаров и извлечения артикулов.

    Атрибуты:
    - link: URL для парсинга.
    - queue_colors: Очередь для хранения ссылок на цвета.
    - queue_article: Очередь для хранения артикулов.
    - options: Настройки для Chrome WebDriver.

    Методы:
    - get_articles: Извлекает артикулы со страницы товара.
    - get_link_colors: Извлекает ссылки на цвета с предоставленной страницы.
    - get_links_goods: Извлекает ссылки на товары из карусели на странице.
    - run: Основной метод потока, обрабатывает очередь цветов.
    """
    def __init__(self, link, queue_colors, queue_article, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--incognito")
        self.options.add_argument('headless')
        self.link = link
        self.set_article = set()
        self.queue_article = queue.Queue()
        self.queue_colors = queue_colors
        self.queue_article = queue_article

    def get_articles(self, link):
        """
        Извлекает артикулы товаров из предоставленной ссылки.

        Аргументы:
        - link: URL страницы для парсинга.

        Возвращает:
        - None. Артикулы добавляются в очередь.
        """
        articles = []

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

        try:
            driver.get(link)
            time.sleep(5)

            table_sises = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="off"][readonly="readonly"]')
            table_sises.click()
            time.sleep(2)

            sises = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')

            count_sises = len(sises)
            driver.refresh()

            for i in range(count_sises):
                element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[autocomplete="off"][readonly="readonly"]')))
                element.click()
                time.sleep(2)

                after_click = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')

                after_click[i].click()
                time.sleep(2)

                search_article = driver.find_element(By.CSS_SELECTOR,
                                                     'button[data-widget="webDetailSKU"]')
                self.queue_article.put(search_article.text+'\n')
        finally:
            driver.quit()

    def get_link_colors(self, link):
        """
        Извлекает все ссылки на цвета с предоставленной ссылки.

        Аргументы:
        - link: URL страницы для парсинга.

        Возвращает:
        - Список ссылок на цвета.
        """
        colors = []
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        driver.get(link)
        time.sleep(5)

        colors_block = driver.find_elements(By.CSS_SELECTOR, 'a[style="border-radius:6px;"]')

        for j in colors_block:
            colors.append(j.get_attribute('href'))

        return colors

    def get_links_goods(self, link):
        """
        Извлекает все ссылки на товары из карусели на предоставленной странице.

        Аргументы:
        - link: URL страницы для парсинга.

        Возвращает:
        - Список ссылок на товары.
        """
        goods_links = []
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        driver.get(link)
        time.sleep(5)

        carousel = driver.find_elements(By.CSS_SELECTOR, 'div[data-widget="skuShelfGoods"]')

        rek_goods = carousel[0].find_elements(By.CSS_SELECTOR, 'a[target="_self"][class*=clickable-element]')

        for j in rek_goods:
            goods_links.append(j.get_attribute('href'))

        return goods_links

    def run(self):
        """
        Основной метод потока. Извлекает ссылки на товары и цвета, обрабатывая очередь цветов.
        """
        while True:
            try:
                color = self.queue_colors.get(timeout=3)
            except Empty:
                break
            print(f'Получена ссылка цвета из очереди: {color}')
            self.get_articles(color)
            carousel_goods = self.get_links_goods(color)
            for n, goods in enumerate(carousel_goods):
                colors = self.get_link_colors(goods)
                for numer, colo in enumerate(colors):
                    try:
                        self.get_articles(colo)
                        writer = Writer(queue_article=self.queue_article)
                        writer.start()
                        writer.join()
                    except Exception:
                        logger_main.debug('Ошибка на url: %s', colo)


class Writer(Thread):
    """
    Потоковый класс для записи артикулов в файл.

    Атрибуты:
    - queue: Очередь для хранения артикулов.

    Методы:
    - run: Основной метод потока, записывает артикулы в файл.
    """
    def __init__(self, queue_article, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue_article

    def run(self):
        """
        Основной метод потока. Извлекает артикулы из очереди и записывает их в файл.
        """
        while True:
            try:
                article = self.queue.get(timeout=6)
            except queue.Empty:
                break
            with open(file='article.txt', mode='a') as file:
                print('Добавил новый артикул')
                file.write(article)
