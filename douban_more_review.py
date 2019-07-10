""""
文件描述：爬取豆瓣影评:为了爬取更多影评，爬取了https://movie.douban.com/subject/30334073/reviews（以电影调音生为例）
作者:xixi2
"""
import re
import time
import numpy as np
import requests
import pandas as pd
from bs4 import BeautifulSoup


def set_header():
    """
    设置爬虫的HTTP头部
    :return:
    """
    header = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6',
        'Connection': 'close',  # 建立短连接，防止被服务器发现是爬虫
        'Host': 'movie.douban.com',
        'Referer': 'https://www.douban.com/accounts/login?source=movie',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    }
    return header


def search(soup):
    comment_list = []
    comments = soup.find_all("div", class_='review-item')
    for comment in comments:
        head_hd = comment.find('header', class_='main-hd')
        head_bd = comment.find('div', class_='main-bd')

        user_name = head_hd.find("a", class_="name").text.strip() if head_hd.find("a", class_="name") else u""  # 用户名
        rating_tag = head_hd.find("span", class_="main-title-rating")  # 打分
        rating = rating_tag.get("title") if rating_tag else u"无评分"
        comment_time_tag = head_hd.find("span", class_="main-meta")
        comment_time = comment_time_tag.text.strip() if comment_time_tag else u"评论时间不存在"
        short_comment = head_bd.contents[1].text.strip() if head_bd.contents[1] else u"尚未有短评"

        long_comment_tag = head_bd.find("div", class_="short-content")
        long_comment = long_comment_tag.text.strip()

        # pos_count:认为有用的人数，neg_count：认为无用的人数, reply_count:回应的人数
        pos_count = head_bd.find("a", class_="action-btn up").text.strip() if head_bd.find("a",
                                                                                           class_="action-btn up") else 0
        neg_count = head_bd.find("a", class_="action-btn down").text.strip() if head_bd.find("a",
                                                                                             class_="action-btn down") else 0
        reply_count = get_number(head_bd.find("a", class_="reply").text.strip()) if head_bd.find("a",
                                                                                                 class_="reply") else 0

        # print("==========================================================================")
        print("user_name: %s, comment_time: %s, rating: %s, pos_count: %s, neg_count: %s, reply_count: %s" % (
            user_name, comment_time, rating, pos_count, neg_count, reply_count))
        print("短评： %s" % short_comment)
        print("长评： %s" % long_comment)
        if user_name or comment_time or rating:
            comment_list.append(
                (user_name, comment_time, rating, pos_count, neg_count, reply_count, short_comment, long_comment))

    return comment_list


def set_cookies():
    # 这里的cookie数据是使用浏览器登录豆瓣之后，从浏览器中copy出来的
    raw_cookies = 'viewed="2000732"; bid=hLr_29qhXqQ; gr_user_id=542149e0-529c-40aa-82d9-1ac0f5705308; ll="108296"; ps=y; _vwo_uuid_v2=7D935E4C5EE5A54CD0ED7FD73DB6486E|52676d78d35275c844d98934cdd100e6; ap=1; dbcl2="155577244:PS9mOEvKstQ"; ck=G5IX; push_noty_num=0; push_doumail_num=0; _pk_id.100001.4cf6=c67059403c59f1c1.1482632518.7.1482843964.1482763369.; _pk_ses.100001.4cf6=*; __utma=30149280.1695826899.1478691770.1482813867.1482843967.9; __utmb=30149280.0.10.1482843967; __utmc=30149280; __utmz=30149280.1482843967.9.3.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/accounts/login; __utmv=30149280.15557; __utma=223695111.710728627.1482632518.1482763017.1482843967.7; __utmb=223695111.0.10.1482843967; __utmc=223695111; __utmz=223695111.1482843967.7.2.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/accounts/login'
    cookies = {}
    for line in raw_cookies.split(';'):
        key, value = line.split('=', 1)  # 1代表只分一次，得到两个数据
        cookies[key] = value
    return cookies


def get_number(s):
    sum = 0
    for i in range(len(s)):
        if '0' <= s[i] <= '9':
            sum = sum * 10 + int(s[i])
        else:
            if sum > 0:
                break
    return sum


def get_info(url, page_first):
    # 发送请求表头，爬取所需要的信息
    header = set_header()

    # 设置cookie，不设置cookie也行，cookie的作用还没有弄明白
    # cookies = set_cookies()
    # data = requests.get(url, timeout=20, headers=header, cookies=cookies).text

    data = requests.get(url, timeout=20, headers=header).text
    soup = BeautifulSoup(data, 'lxml')
    comment_list = search(soup)

    total_num = 0
    # 若是第一页
    if page_first:
        total_text = soup.find("span", "count").text.strip()
        total_num = get_number(total_text)
        print("total_num:", total_num)
    return comment_list, total_num


def save2csv(comments_dict, fields, csv_file):
    df = pd.DataFrame(comments_dict, columns=fields)
    df.to_csv(csv_file)


def split_comment_list(comment_list):
    users, comment_times, ratings, pos_counts, neg_counts, reply_counts, short_comments, long_comments = [[]] * 8
    for user_name, comment_time, rating, pos_count, neg_count, reply_count, short_comment, long_comment in comment_list:
        users.append(user_name)
        comment_times.append(comment_time)
        ratings.append(rating)
        pos_counts.append(pos_count)
        neg_counts.append(neg_count)
        reply_counts.append(reply_count)
        short_comments.append(short_comment)
        long_comments.append(long_comment)
    return users, comment_times, ratings, pos_counts, neg_counts, reply_counts, short_comments, long_comments


if __name__ == '__main__':
    # 要爬取的电影的id及电影名：要添加电影，只需要将将电影的id及其对应的电影名加入到movie_dict中就行，电影的id直接在豆瓣搜索，从URL中截取出来
    movie_dict = {
        "26584183": "权利的游戏第8季", "27060077": "绿皮书 Green Book", "30334073": "调音师 Andhadhun",
        "26266893": "流浪地球", "30163509": "飞驰人生", "26100958": "复仇者联盟4"
    }
    movie_ids = list(movie_dict.keys())

    # 依次爬取每个电影的评论
    url_common = "https://movie.douban.com/subject/%s/reviews"
    for movie_id in movie_ids:
        # 初始化comment_dict
        comment_dict = {"user_name": [], "watched": [], "comment_time": [], "rating": [], "pos_count": [],
                        "neg_count": [], "reply_count": [], "short_comment": [], "long_comment": []}

        url = (url_common + "?status=P") % (movie_id,)
        page_num = 0  # 页码，第一页的页码为0，第二页为1,以此类推
        total_reviews = 0  # 总页数
        while 1:
            comment_list, total_num = get_info(url, page_num == 0)
            users, comment_times, ratings, pos_counts, neg_counts, reply_counts, short_comments, long_comments = split_comment_list(
                comment_list)
            comment_dict["user_name"].extend(users)
            comment_dict["comment_time"].extend(comment_times)
            comment_dict["rating"].extend(ratings)
            comment_dict["pos_count"].extend(pos_counts)
            comment_dict["neg_count"].extend(neg_counts)
            comment_dict["reply_count"].extend(reply_counts)
            comment_dict["short_comment"].extend(short_comments)
            comment_dict["long_comment"].extend(long_comments)

            # 如果当前爬取的是第一页，则设置总的评论条数
            if not page_num:
                total_reviews = total_num
            else:
                if (page_num + 1) * 20 >= total_reviews:
                    break
            # 睡眠一会，继续爬取下一页
            time.sleep(np.random.rand() * 5)
            page_num += 1  # 设置接下来爬取的页码
            url = (url_common + "?start=%s") % (movie_id, page_num * 20)
            print("url: %s" % url)

        if comment_dict:
            print("totally capture %s comments for movie %s" % (len(comment_dict.get("user_name", [])), movie_id))
            fields = ["user_name", "comment_time", "rating", "pos_count", "neg_count", "reply_count", "short_comment",
                      "long_comment"]
            csv_file = movie_dict.get(movie_id) + "_more.csv"  # 每一部电影保存到一个csv文件中，文件名是电影⍳d
            save2csv(comment_dict, fields, csv_file)
