import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import urllib.parse as urlparse
import re
import json
import time
import sys


class WebAccess:
    def __init__(self, mode='static'):
        if mode == 'dynamic':
            self.driver = webdriver.Chrome()
            self.driver.maximize_window()
            time.sleep(2)

        else:
            self.driver = None
        self.mode = mode
        self.access_num = 0  # 动态访问计数
        self.first_access_time = 4         # 第一次访问网站时给的爬取网页的时间延迟
        self.refresh_access_time = 2.5       # 第二次及以后访问网站时给的爬取网页的时间延迟

    def __del__(self):
        if self.driver:
            self.driver.close()
            self.driver = None

    def get_page(self, page):  # 获取网页

        if self.mode == 'static':
            try:
                header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                        '(KHTML, like Gecko)'
                                        ' Chrome/81.0.4044.138 Safari/537.36'}
                r = requests.get(page, headers=header, timeout=30)
                r.raise_for_status()
                # 不是200则爬出http error
                # print(r.encoding, r.apparent_encoding)
                r.encoding = r.apparent_encoding
                return r.text
            except:
                return "Error. Page Not Found."
        elif self.mode == 'dynamic' and self.driver:
            self.access_num += 1
            try:
                self.driver.get(page)
                if self.access_num == 1:      # 第一次访问时较慢，给一个较大的延迟
                    time.sleep(self.first_access_time)
                else:
                    time.sleep(self.refresh_access_time)
                data = self.driver.page_source
                return data
            except:
                return "Error. Page Not Found."
        else:
            return "Error Mode or driver closed."

    @staticmethod
    def write_page(file_name, page):
        page = page.encode('utf-8')
        with open(file_name + '.html', 'wb') as f:
            f.write(page)


class MainEngine:
    def __init__(self):
        self.explorer = WebAccess('dynamic')        # 动态访问浏览器
        self.static_exp = WebAccess('static')       # 静态访问浏览器

    def get_dynamic_page(self, url):  # 获取动态网页
        webpage = self.explorer.get_page(url)
        # self.explorer.write_page('temp_dynamic_page', webpage)
        return webpage

    def get_page(self, url):  # 获取静态网页
        webpage = self.static_exp.get_page(url)
        # self.static_exp.write_page('temp_static_page', webpage)
        return webpage

    def abc_search(self, keyword):  # 根据搜索词进行单次搜索并返回网页
        url_code_keyword = urlparse.quote(keyword)
        url = "https://search-beta.abc.net.au/#/?query=" + url_code_keyword + \
              "&page=1&configure%5BgetRankingInfo%5D=true&configure%5BclickAnalytics%5D=true&configure%5" \
              "BuserToken%5D=anonymous-7cc09af2-9d44-4469-96b6-cb74027e2671&configure%5Banalytics%5D=true" \
              "&refinementList%5Bsite.title%5D%5B0%5D=ABC%20News"
        # print(url)
        search_result = self.explorer.get_page(url)
        # self.explorer.write_page('temp', search_result)    # 存储搜索结果页面
        return search_result

    def get_news(self, url):
        if url:
            return self.get_page(url)
        else:
            return None


class PageParse:
    @staticmethod
    def find_first_abc_news(search_html):  # 搜索结果页分析，返回第一个新闻链接url
        whole_page = BeautifulSoup(search_html, 'html.parser')
        news_list = whole_page.find_all(attrs={'class': '', 'data-component': 'ListItem', 'data-test': 'search-hit'})
        link = None
        pattern = re.compile(r'.*https://www.abc.net.au/news/.*')
        for news in news_list:
            news_content = news.find(attrs={'data-component': 'Link'})
            href = news_content.get('href')
            if pattern.match(href):
                link = href
                # print(link)
                break
        return link

    @staticmethod
    def abc_news_parse_1(news_html):  # 新闻网页分析，返回分析字典
        whole_page = BeautifulSoup(news_html, 'html.parser')  # 全网页
        news_body = whole_page.find(attrs={'id': 'body'})  # 正文
        # print(news_body)

        # 获取照片url列表
        image_urls = []
        # 正文图片目前分析出class属性有一定规律
        figures = whole_page.find_all('figure', attrs={'class': re.compile(r"^_3M2Ue _1LbdU _1bAUU.*"),
                                                       'role': "group", 'data-component': "Figure"})
        if figures:
            for figure in figures:
                image_urls.append(figure.find('noscript').img.get('src'))
        # print(image_urls)

        # 抽取时间
        pub_time = whole_page.find(attrs={'data-component': 'PublishedDate'}).time
        time_text = pub_time.get('datetime')
        time_text = time_text[0:10] + ' ' + time_text[11:19]
        # print(time_text)

        # 来源
        source = 'abc.au'

        # 获取标题
        title_pos = whole_page.find('h1', attrs={'data-component': "Heading"})
        title_text = title_pos.get_text()
        # print(title_text)

        # 获取url
        url_pos = whole_page.find('meta', attrs={'data-react-helmet': "true", 'property': "og:url"})
        url_text = url_pos.get('content')
        # print(url_text)

        # 抽取新闻文本
        news_paragraphs = news_body.find_all('p', attrs={'class': '_1SzQc'})
        # print(news_paragraphs)
        news_text = ""
        for paragraph in news_paragraphs:
            news_text += (paragraph.get_text() + '\n')
        # print(news_text)

        result_dict = {"image": image_urls, "pub_time": time_text, "source": source,
                       "title": title_text, "url": url_text, "content": news_text, "valid": "True"}

        return result_dict

    @staticmethod
    def abc_news_parse_2(news_html):           # 有一些新闻网页内仅有一张图片或一个视频加以描述，主体并非文字
        whole_page = BeautifulSoup(news_html, 'html.parser')  # 全网页

        # 新闻种类有ABCAudio
        news_type = whole_page.find('meta', attrs={'name': 'ABC.ContentType'}).get('content')
        if news_type == 'ABCAudio':
            news_body = whole_page.find('div', attrs={'class': 'comp-rich-text clearfix'})  # 正文
        else:
            news_body = whole_page.find('div', attrs={'class': 'article section'})  # 正文
        # print(news_body)

        # 获取照片url列表
        image_urls = []
        # 正文图片目前分析出class属性有一定规律
        figures = whole_page.find_all('figure', attrs={'class': re.compile(r"^_3M2Ue _1LbdU _1bAUU.*"),
                                                       'role': "group", 'data-component': "Figure"})
        if figures:
            for figure in figures:
                image_urls.append(figure.find('noscript').img.get('src'))
        # print(image_urls)

        # 抽取时间
        pub_time = whole_page.find('meta', attrs={'name': re.compile(r".*\.date")})
        time_text = pub_time.get('content')
        time_text = time_text[0:10] + ' ' + time_text[11:19]
        # print(time_text)

        # 来源
        source = 'abc.au'

        # 获取标题
        title_pos = whole_page.find('meta', attrs={'name': "title"})
        title_text = title_pos.get('content')
        # print(title_text)

        # 获取url
        url_pos = whole_page.find('link', attrs={'rel': "canonical"})
        url_text = url_pos.get('href')
        # print(url_text)

        # 抽取新闻文本
        news_paragraphs = news_body.find_all('p')
        # print(news_paragraphs)
        news_text = ""
        for paragraph in news_paragraphs:
            if not paragraph.get('class'):              # 这类新闻仅仅有一段不带任何属性的文本
                news_text += (paragraph.get_text() + '\n')
                break
        # print(news_text)

        result_dict = {"image": image_urls, "pub_time": time_text, "source": source,
                       "title": title_text, "url": url_text, "content": news_text, "valid": "True"}

        return result_dict

    @staticmethod
    def abc_news_parse(news_html):  # 总控制逻辑
        try:
            return 'mode1', PageParse.abc_news_parse_1(news_html)    # 先尝试模式1
        except Exception as e1:
            return 'mode2', PageParse.abc_news_parse_2(news_html)     # 再尝试模式2

    @staticmethod
    def abc_news_nan():     # 占位的空新闻
        result_dict = {"image": [], "pub_time": "", "source": "", "title": "",
                       "url": "", "content": "", "valid": "False"}
        return result_dict


def main(news_txt, load_flag=False):
    with open(news_txt, 'r', encoding='UTF-8') as f:
        news = f.read()
        news = news.split('\n')

    # print(news)

    search = MainEngine()  # 爬虫主引擎

    # 计数器
    target_num = len(news)
    acc_num = 0
    valid_num = 0

    news_json = []  # 存储查找结果列表

    if load_flag:
        with open("result.json", 'r') as json_file:     # 读取
            news_json = json.load(json_file)
            print("Load Json File with {} Previous News.".format(len(news_json)))

    for item in news:
        acc_num += 1
        if not acc_num > len(news_json):         # 跳过已经爬取过的部分
            continue
        search_result = search.abc_search(item)
        news_url = PageParse.find_first_abc_news(search_result)  # 寻找到搜索结果中第一条新闻的 url
        if news_url:
            try:
                news_html = search.get_news(news_url)  # 获取到新闻网页
                mode, result = PageParse.abc_news_parse(news_html)
                news_json.append(result)  # 新闻网页中提取信息
                valid_num += 1
                print("Success: ({}/{}) {} ".format(acc_num, target_num, mode), item)
            except Exception as e:
                news_json.append(PageParse.abc_news_nan())  # 空信息
                print("Error: ({}/{})".format(acc_num, target_num), item)
                # break      # 出错时终止程序

        else:  # url为空证明搜索新闻结果为空
            news_json.append(PageParse.abc_news_nan())  # 空信息
            print("Nan: ({}/{})".format(acc_num, target_num), item)

    # Summary
    print("Total {} news, search {} news, valid {} news.".format(target_num, acc_num, valid_num))
    with open("result.json", 'w') as f:  # 爬取结束，进行存储
        json.dump(news_json, f)

    # with open("result.json", 'r') as f:     # 读取
    #     news_list = json.load(f)


if __name__ == '__main__':
    news_file = sys.argv[1]
    if sys.argv[2] == 'load':
        load = True
    else:
        load = False
    # news_file = 'news.txt'
    main(news_file, load)
