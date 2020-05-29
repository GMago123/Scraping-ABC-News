# ABC网站新闻爬取

- 运行方式： python main.py XXX.txt
- XXX.txt是存储标题的文本文件，每一行是一个标题
- 环境依赖：selenium这里采用chrome浏览器作为驱动，所以浏览器需要下载chromedriver.exe放在谷歌浏览器文件夹下，并添加环境变量，程序才可以正常运行



### 源码说明

##### **WebAccess**浏览器模块

功能：建立连接获取html网页

- init(mode)：mode=‘static’或‘dynamic’，静态网页爬取利用request，动态网页爬取利用selenium

- init函数里面有时间参数，如果时间延迟过小，会导致爬虫抓到的数据有错位，甚至可能发生错误

  - ```python
    self.first_access_time = 4  # 第一次访问网站时给的爬取网页的时间延迟，因为ABC网站第一次进入较慢
    ```

  - ```python
    self.refresh_access_time = 2.5   # 第二次及以后访问网站时给的爬取网页的时间延迟，ABC搜索速度第二次以后较快
    ```

- get_page(self, page)：page是要访问页面的url，返回网页结果html或错误信息
- write_page(file_name, page)：将html对象（page）写入文件（file_name）

**MainEngine主引擎模块**

功能：处理新闻搜索逻辑并获得搜索结果

- init()：初始化一个静态浏览器和一个动态浏览器
- get_dynamic_page(self, url)：输入url，以动态模式访问并返回html
- get_page(self, url)：输入url，以静态模式访问并返回html
- abc_search(self, keyword)：输入一个用于搜索的字符串keyword，返回ABC搜索结果网页
- get_news(self, url)：输入新闻url，返回新闻网页（这一步仅仅较get_page多添加了一个检测是否为空的机制）

**PageParse网页分析模块（静态类）**

功能：输入html文件并根据检索规则返回一定的信息获取结果

- find_first_abc_news(search_html)：给定ABC搜索结果网页，找出搜索结果中的第一条新闻
- abc_news_parse(news_html)：给定ABC新闻网页，寻找相关信息，以字典形式保存方便转换为json



**主函数**

main(news_txt)

- 输入news_txt作为要搜索的新闻的存储路径，文件应为txt且一行为一个检索文本
- 获取到要搜索的列表，逐个执行搜索、解析过程，最终将所有新闻信息储存在result.json文件中