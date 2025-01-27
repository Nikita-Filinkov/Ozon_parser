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


class Parser(Thread):
    """
    Потоковый класс для парсинга ссылок на цвета и товары.

    Атрибуты:
    - queue_colors: Очередь для хранения ссылок на цвета.
    - first_colors: Очередь для хранения первоначальных цветов.
    - options: Настройки для Chrome WebDriver.

    Методы:
    - get_link_colors: Извлекает ссылки на цвета с заданной страницы.
    - get_links_goods: Извлекает ссылки на товары из карусели на странице.
    - run: Основной метод потока, обрабатывает очередь цветов.
    """
    def __init__(self, queue_colors, first_colors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36")  # Замените на актуальный User-Agent
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--incognito")
        self.options.add_argument('headless')

        self.first_colors = first_colors
        self.queue_colors = queue_colors

    def get_link_colors(self, link):
        """
        Извлекает все ссылки на цвета с предоставленной ссылки.

        Аргументы:
        - link: URL страницы для парсинга.

        Возвращает:
        - Список ссылок на цвета.
        """
        goods_links = []
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        driver.get(link)
        time.sleep(2)

        colors_block = driver.find_elements(By.CSS_SELECTOR, 'a[style="border-radius:6px;"]')

        for j in colors_block:
            self.queue_colors.put(j.get_attribute('href'))
            print("Добавил цвет в очередь")
            goods_links.append(j.get_attribute('href'))

        return goods_links

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
        time.sleep(2)

        carousel = driver.find_elements(By.CSS_SELECTOR, 'div[data-widget="skuShelfGoods"]')
        if not carousel:
            return []

        rek_goods = carousel[0].find_elements(By.CSS_SELECTOR, 'a[target="_self"][class*=clickable-element]')

        for j in rek_goods:
            goods_links.append(j.get_attribute('href'))

        return goods_links

    def run(self):
        """
        Основной метод потока. Извлекает ссылки на товары и цвета, обрабатывая очередь первичных цветов.
        """
        while True:
            try:
                color = self.first_colors.get(timeout=1)
                print(f'Получен цвет из очереди первичных цветов: {color}')
            except Empty:
                print('очередь пуста')
                break
            carousel_goods = self.get_links_goods(color)
            if not carousel_goods:
                continue
            try:
                for n, goods in enumerate(carousel_goods):
                    self.get_link_colors(goods)
            except Exception:
                logger_main.debug('Ошибка на url: %s', goods)


class Article(Thread):
    """
    Потоковый класс для извлечения артикулов товаров.

    Атрибуты:
    - queue_colors: Очередь ссылок на цвета.
    - queue_article: Очередь для хранения артикулов.

    Методы:
    - get_articles: Извлекает артикула со страницы товара.
    - run: Основной метод потока, обрабатывает очередь цветов.
    """
    def __init__(self, queue_colors, queue_article, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36")  # Замените на актуальный User-Agent
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--incognito")
        self.options.add_argument('headless')
        self.queue_colors = queue_colors
        self.queue_article = queue_article

    def get_articles(self):
        """
        Извлекает артикулы товаров из ссылок, хранящихся в очереди цветов.
        """
        while True:
            try:
                link = self.queue_colors.get(timeout=20)
                print("Взял цвет")
            except queue.Empty:
                print('Очередь цветов пуста')
                break
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            try:
                driver.get(link)
                time.sleep(2)

                table_sises = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="off"][readonly="readonly"]')
                table_sises.click()
                time.sleep(2)

                sises = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')

                count_sises = len(sises)
                if count_sises < 1:
                    continue
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
                    article = search_article.text + '\n'
                    self.queue_article.put(article)
                    print(f"Добавил новый артикул в очередь: {article}")
            finally:
                driver.quit()

    def run(self):
        """
        Основной метод потока. Запускает извлечение артикулов.
        """
        self.get_articles()


class Writer(Thread):
    """
    Потоковый класс для записи артикулов в файл.

    Атрибуты:
    - queue_article: Очередь для хранения артикулов.

    Методы:
    - run: Основной метод потока, записывает артикулы в файл.
    """
    def __init__(self, queue_article, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_article = queue_article

    def run(self):
        """
        Основной метод потока. Извлекает артикулы из очереди и записывает их в файл.
        """
        while True:
            try:
                article = self.queue_article.get(timeout=50)
                print(article)
            except queue.Empty:
                print('Пустая очередь писателя')
                break
            with open(file='article.txt', mode='r') as f:
                for line in f.readline():
                    if article in line:
                        print(f'Такой артикул уже есть: {line} = {article}')
                        continue
                with open(file='article.txt', mode='a') as file:
                    file.write(article)
                    print(f'Записал в файл новый артикул: {article}')


class FullPower(Thread):
    """
    Основной потоковый класс, который управляет всеми другими потоками.

    Атрибуты:
    - link: URL для парсинга.
    - queue_article: Очередь для хранения артикулов.
    - queue_colors: Очередь для хранения ссылок на цвета.
    - first_colors: Очередь для хранения первоначальных цветов.
    - parsers: Список потоков парсеров.
    - articles: Список потоков для извлечения артикулов.
    - writers: Список потоков для записи артикулов.

    Методы:
    - add_parser: Добавляет потоки парсеров.
    - add_article: Добавляет потоки для извлечения артикулов.
    - add_writer: Добавляет потоки для записи артикулов.
    - fulling_queue: Заполняет очередь первичных цветов.
    - run: Основной метод потока, запускает все остальные потоки.
    """
    def __init__(self, link, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_article = queue.Queue()
        self.queue_colors = queue.Queue()
        self.first_colors = queue.Queue()
        self.link = link
        self.parsers = []
        self.articles = []
        self.writers = []

    def add_parser(self):
        """
        Добавляет потоки парсеров, которые будут извлекать ссылки на цвета и товары.
        """
        for _ in range(2):
            parser = Parser(queue_colors=self.queue_colors, first_colors=self.first_colors)
            self.parsers.append(parser)
            parser.start()

    def add_article(self):
        """
        Добавляет потоки для извлечения артикулов товаров.
        """
        for _ in range(5):
            article = Article(queue_colors=self.queue_colors, queue_article=self.queue_article)
            self.articles.append(article)
            article.start()

    def fulling_queue(self):
        """
        Заполняет очередь первичных цветов, извлекая ссылки на цвета с заданной страницы.

        Возвращает:
        - Список ссылок на цвета.
        """
        first_colors = []
        options = webdriver.ChromeOptions()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument('headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(self.link)
        time.sleep(3)

        colors_block = driver.find_elements(By.CSS_SELECTOR, 'a[style="border-radius:6px;"]')

        for j in colors_block:
            self.first_colors.put(j.get_attribute('href'))
            first_colors.append(j.get_attribute('href'))

        return first_colors

    def add_writer(self):
        """
        Добавляет потоки для записи артикулов в файл.
        """
        for _ in range(2):
            writer = Writer(queue_article=self.queue_article)
            self.writers.append(writer)
            writer.start()

    def run(self):
        """
        Основной метод потока. Запускает процесс заполнения очереди и все остальные потоки.
        """
        self.fulling_queue()
        print("Загрузил очередь первых цветов")
        self.add_parser()
        self.add_article()
        self.add_writer()

        print("Добавил парсеров и артиклов")
        for pars in self.parsers:
            pars.join()
        for article in self.articles:
            article.join()
        for writer in self.writers:
            writer.join()
