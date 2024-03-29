class Artists:
    def __init__(self, url, name):
        self.url = url
        self.name = name

    def get_page(self):
        n = 0
        with ThreadPoolExecutor() as executor:  # max_workers 最大线程数，总线程为三个最大线程的乘积。
            while True:
                url = f"{self.url}?o={n}"
                r = requests.get(url, allow_redirects=False)
                if r.is_redirect:
                    break
                executor.submit(Page(url).get_posts)
                n += 50


class Page:
    def __init__(self, page_url):
        self.url = page_url

    def get_posts(self):
        r = requests.get(self.url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            article = soup.find_all('article', class_='post-card post-card--preview')
            if article:
                with ThreadPoolExecutor() as executor:  # 最大线程数
                    total_tasks = len(article)
                    futures = []

                    with tqdm(
                            total=total_tasks, desc=f"下载中...", unit="posts", unit_scale=True, unit_divisor=1, ncols=100
                    ) as pbar:
                        for i in article:
                            a_tag = i.find('a')
                            if a_tag:
                                posts_url = a_tag.get('href')
                                # Posts(posts_url).download_img()
                                future = executor.submit(Posts(posts_url).download_img)
                                futures.append(future)

                        for _ in as_completed(futures):
                            pbar.update(1)
                    pbar.close()
        elif r.status_code == 429:
            # print("请求过快")
            time.sleep(random.randint(1, 10))
            self.get_posts()




class Posts:
    def __init__(self, posts_url):
        self.url = posts_url

    def download_img(self):
        try:
            url = f"https://kemono.su{self.url}"
            r = requests.get(url)
            if r.status_code == 200:
                image_links = re.findall(r'href="(https?://c(?!h).*?)"', r.text)
                soup = BeautifulSoup(r.text, 'html.parser')
                h1_tag = soup.find('h1', class_='post__title')
                # title_text = h1_tag.get_text(strip=True)
                title_text = pathvalidate.sanitize_filename(h1_tag.get_text(strip=True))
                path = f"{os.path.expanduser('~')}\\Desktop\\download\\{title_text}\\"
                if not os.path.exists(path):
                    os.makedirs(path)
                with ThreadPoolExecutor(max_workers=200) as executor:  # 最大线程数

                    for link in image_links:
                        parsed_url = urlparse(link)
                        file_name = os.path.basename(parsed_url.path)

                        img_path = f"{path}{file_name}"

                        executor.submit(self.download_image, link, img_path)
            elif r.status_code == 429:
                # print("下载过快")
                time.sleep(random.randint(1, 10))
                self.download_img()

        except Exception as e:
            print(f"错误{self.url},{e}")

    @staticmethod
    def download_image(link, img_path):

        while True:
            if os.path.exists(img_path):
                break
            r = requests.get(link)
            if r.status_code == 200:
                with open(img_path, 'wb') as file:
                    file.write(r.content)
                break
            else:
                time.sleep(random.randint(1, 10))



if __name__ == '__main__':
    p = Artists(input("请输入链接,默认下载在桌面download文件夹内。\n"), "a")
    p.get_page()
    input("按回车关闭")
