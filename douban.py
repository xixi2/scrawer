""""
文件描述：爬取豆瓣影评
作者:xixi2
"""
import re
import time
import numpy as np
import requests
import pandas as pd
from bs4 import BeautifulSoup


def set_header():
    header = dict()
    header['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    header['Accept-Encoding'] = 'gzip, deflate, sdch, br'
    header['Accept-Language'] = 'zh-CN,zh;q=0.8,zh-TW;q=0.6'
    header['Connection'] = 'keep-alive'
    header['Host'] = 'movie.douban.com'
    header['Referer'] = 'https://www.douban.com/accounts/login?source=movie'
    header[
        'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
    return header


def search(soup):
    comment_list = []
    comments = soup.find_all("div", class_='comment-item')
    for comment in comments:
        comment_info = comment.find('span', class_='comment-info')
        comment_vote = comment.find('span', class_='comment-vote')
        user_name = comment_info.contents[1].text.strip()  # 用户名

        # 是否看过,还是想看
        watched = comment_info.contents[3].text.strip()

        # 评论时间
        comment_time = comment.find("a", class_="comment-time")
        comment_time = comment_time.get("title") if comment_time else u"评论时间不存在"

        # 打分
        rating = comment.find('span', class_="rating")
        rating = rating.get("title") if rating else u"无评分"

        # 短评
        short_comment = comment.find("span", class_="short")
        short_comment = short_comment.text.strip() if short_comment else u"未评论"

        voting = comment_vote.find("span", class_="votes").text.strip()

        print("==========================================================================")
        print("user_name: %s, watched: %s, comment_time: %s, rating: %s, voting: %s" % (
            user_name, watched, comment_time, rating, voting))
        print("短评： %s" % short_comment)
        if user_name or watched or comment_time or rating:
            comment_list.append((user_name, watched, comment_time, rating, voting, short_comment))
    return comment_list


def set_cookies():
    # 这里的cookie数据是使用浏览器登录豆瓣之后，从浏览器中copy出来的
    raw_cookies = 'viewed="2000732"; bid=hLr_29qhXqQ; gr_user_id=542149e0-529c-40aa-82d9-1ac0f5705308; ll="108296"; ps=y; _vwo_uuid_v2=7D935E4C5EE5A54CD0ED7FD73DB6486E|52676d78d35275c844d98934cdd100e6; ap=1; dbcl2="155577244:PS9mOEvKstQ"; ck=G5IX; push_noty_num=0; push_doumail_num=0; _pk_id.100001.4cf6=c67059403c59f1c1.1482632518.7.1482843964.1482763369.; _pk_ses.100001.4cf6=*; __utma=30149280.1695826899.1478691770.1482813867.1482843967.9; __utmb=30149280.0.10.1482843967; __utmc=30149280; __utmz=30149280.1482843967.9.3.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/accounts/login; __utmv=30149280.15557; __utma=223695111.710728627.1482632518.1482763017.1482843967.7; __utmb=223695111.0.10.1482843967; __utmc=223695111; __utmz=223695111.1482843967.7.2.utmcsr=douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/accounts/login'
    cookies = {}
    for line in raw_cookies.split(';'):
        key, value = line.split('=', 1)  # 1代表只分一次，得到两个数据
        cookies[key] = value
    return cookies


def get_info(url):
    # 发送请求表头，爬取所需要的信息
    page_num = 0
    header = set_header()

    # 设置cookie，不设置cookie也行，cookie的作用还没有弄明白
    # cookies = set_cookies()
    # data = requests.get(url, timeout=20, headers=header, cookies=cookies).text

    data = requests.get(url, timeout=20, headers=header).text
    soup = BeautifulSoup(data, 'lxml')
    comment_list = search(soup)
    pattern = re.compile(r'a href="(.*?)" data-page="" class="next"')
    page_next = re.findall(pattern, data)
    page_num += 1
    return comment_list, page_next


def save2csv(comments_dict, fields, csv_file):
    df = pd.DataFrame(comments_dict, columns=fields)
    df.to_csv(csv_file)


def comment_list2dict(comment_list):
    comment_dict = {"user_name": [], "watched": [], "comment_time": [], "rating": [], "voting": [], "short_comment": []}
    for user_name, watched, comment_time, rating, voting, short_comment in comment_list:
        comment_dict["user_name"].append(user_name)
        comment_dict["watched"].append(watched)
        comment_dict["comment_time"].append(comment_time)
        comment_dict["rating"].append(rating)
        comment_dict["voting"].append(voting)
        comment_dict["short_comment"].append(short_comment)
    return comment_dict


def split_comment_list(comment_list):
    users, watched_list, comment_times, ratings, votings, short_comment_list = [], [], [], [], [], []
    for user_name, watched, comment_time, rating, voting, short_comment in comment_list:
        users.append(user_name)
        watched_list.append(watched)
        comment_times.append(comment_time)
        ratings.append(rating)
        votings.append(voting)
        short_comment_list.append(short_comment)
    return users, watched_list, comment_times, ratings, votings, short_comment_list


if __name__ == '__main__':
    # 要爬取的电影的id及电影名：要添加电影，只需要将将电影的id及其对应的电影名加入到movie_dict中就行，电影的id直接在豆瓣搜索，从URL中截取出来
    movie_dict = {
        "26584183": "权利的游戏第8季", "27060077": "绿皮书 Green Book", "30334073": "调音师 Andhadhun",
        "26266893": "流浪地球", "30163509": "飞驰人生", "26100958": "复仇者联盟4"
    }
    movie_ids = list(movie_dict.keys())

    # 依次爬取每个电影的评论
    url_common = "https://movie.douban.com/subject/%s/comments"
    for movie_id in movie_ids:
        # 初始化comment_dict
        comment_dict = {"user_name": [], "watched": [], "comment_time": [], "rating": [], "voting": [],
                        "short_comment": []}

        url = (url_common + "?status=P") % (movie_id,)
        while 1:
            comment_list, page_next = get_info(url)
            users, watched_list, comment_times, ratings, votings, short_comment_list = split_comment_list(comment_list)
            comment_dict["user_name"].extend(users)
            comment_dict["watched"].extend(watched_list)
            comment_dict["comment_time"].extend(comment_times)
            comment_dict["rating"].extend(ratings)
            comment_dict["voting"].extend(votings)
            comment_dict["short_comment"].extend(short_comment_list)

            # if comment_dict.get("user_name"):
            #     print("len of users: %s" % (len(comment_dict["user_name"])))

            # 睡眠一会，继续爬取下一页
            time.sleep(np.random.rand() * 5)
            if page_next:
                page_num_info = re.sub(r'amp;', '', page_next[0])
                url = (url_common + page_num_info) % (movie_id,)  # 翻页url
            else:
                break
        if comment_dict:
            print("totally capture %s comments for movie %s" % (len(comment_dict.get("user_name", [])), movie_id))
            fields = ["user_name", "watched", "comment_time", "rating", "voting", "short_comment"]
            csv_file = movie_id + ".csv"  # 每一部电影保存到一个csv文件中，文件名是电影⍳d
            save2csv(comment_dict, fields, csv_file)
