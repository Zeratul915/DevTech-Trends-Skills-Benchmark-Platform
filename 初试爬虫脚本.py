import requests
from bs4 import BeautifulSoup
import time
from utils.logger import setup_logger

logger = setup_logger('github_trending')

def fetch_trending_page(since='daily', language=''):
    """
    抓取 GitHub Trending 单页数据（最多25个项目）
    :param since: daily, weekly, monthly
    :param language: 编程语言过滤，如 'python'
    """
    url = f'https://github.com/trending/{language}?since={since}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, 'lxml')
    repos = []
    # 定位每个仓库卡片
    articles = soup.select('article.Box-row')
    for article in articles:
        h2 = article.find('h2')
        if not h2:
            continue
        # 标题处理：去掉换行和多余空格
        title = h2.text.strip().replace('\n', '').replace(' ', '')
        # 简介
        desc_p = article.find('p', class_='col-9')
        description = desc_p.text.strip() if desc_p else ''
        repos.append({
            'title': title,
            'description': description,
            'source': 'github_trending'
        })
    logger.info(f"抓取到 {len(repos)} 个项目")
    return repos

if __name__ == '__main__':
    # 测试单页抓取
    data = fetch_trending_page()
    for repo in data[:5]:
        print(f"{repo['title']}: {repo['description'][:50]}...")
