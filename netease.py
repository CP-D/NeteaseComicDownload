# coding: utf-8

"""
python netease.py number [start]
  -- number : The number at the end of the URL where your comic is located.
  -- start : Download will start from the specified chapter. The default value of "start" is 1.
Here is an example:
If you want to download comic on https://manhua.163.com/source/4499978832940093552 from chapter 10 to the end,
you can execute "python netease.py 4499978832940093552 10".
"""

import urllib
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time
import os
import sys

if __name__ == "__main__":
    arg_len = len(sys.argv)
    if arg_len < 2:
        print "Target number is not found. Please use help(netease) in python command line and read the details."
        exit(1)
    else:
        url = "https://manhua.163.com/source/" + sys.argv[1]

    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(1)
    driver.find_element_by_class_name("j-toggle-order").click()
    time.sleep(1)
    driver.find_element_by_class_name("j-load-more-button").click()
    time.sleep(1)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    title = bs.find("title").text.encode('utf8')
    if not os.path.exists(title):
        os.mkdir(title)

    cover_tag = bs.find("img", {'class': 'sr-bcover'})
    urllib.urlretrieve(cover_tag['src'], "./" + title + "/cover.jpg")

    chapters = bs.findAll("a", {'data-log':re.compile('b1-14.+')})
    skip = 1
    if arg_len > 2:
        skip = int(sys.argv[2])

    for chapter in chapters:
        if skip > 1:
            skip = skip - 1
            continue

        chapter_title = chapter.attrs.get('title').encode('utf8')
        print "Start downloading : " + chapter_title
        print "Url : " + "https://manhua.163.com" + chapter['href']

        index = 0
        dir = title + "/" + chapter_title
        if not os.path.exists(dir):
            os.makedirs(dir)
        dir_trans = dir.replace(" ", "\\ ").replace("(", "\\(").replace(")", "\\)")
        while True:
            driver.get("https://manhua.163.com" + chapter['href'] + "#scale=7@imgIndex=" + str(index))
            time.sleep(1)
            html = driver.page_source
            bs = BeautifulSoup(html, "html.parser")


            rightbox = bs.find("div", {'class': 'img-box-rightin'})
            if rightbox != None:
                rightimg = rightbox.find("img")['src']
                urllib.urlretrieve(rightimg, "./" + dir + "/" + str(index) + ".webp")
                os.system('dwebp ' + "./" + dir_trans + "/" + str(index) + ".webp -o " + "./" + dir_trans + "/" + str(index) + ".jpg")
                os.remove("./" + dir + "/" + str(index) + ".webp")
                index = index + 1

            leftbox = bs.find("div", {'class': 'img-box-leftin'})
            if leftbox != None:
                leftimg = leftbox.find("img")['src']
                urllib.urlretrieve(leftimg, "./" + dir + "/" + str(index) + ".webp")
                os.system('dwebp ' + "./" + dir_trans + "/" + str(index) + ".webp -o " + "./" + dir_trans + "/" + str(index) + ".jpg")
                os.remove("./" + dir + "/" + str(index) + ".webp")
                index = index + 1
            else:
                break

    print "Download Finished..."
    driver.close()
