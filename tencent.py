from selenium import webdriver
import argparse
import time
import urllib.request as req
import re
import shutil
import os
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='Tecent comic download.')
parser.add_argument('--id', type=str, default='626438')
parser.add_argument('--start', type=int, default=109)
parser.add_argument('--end', type=int, default=0)
args = parser.parse_args()
url = "https://dm.vip.qq.com/club/client/ipadComic/html/large-scale/comic/detail.html?id="+args.id

# open the website
driver = webdriver.Firefox()
driver.get(url)
time.sleep(1)

# block until login
while True:
    time.sleep(1)
    try:
        a = driver.find_element_by_tag_name("iframe")
    except:
        break

n = -1
while True:
    n += 1
    try:
        nav = driver.find_elements_by_class_name("swiper-slide")[n]
    except:
        print("Finish.")
        exit(0)
    if nav.tag_name != "li":
        continue
    nav.click()
    first_chapter = int(nav.text.split('-')[0])
    last_chapter = int(nav.text.split('-')[1])

    i = -1
    while True:
        i += 1
        chapter = first_chapter + i
        if chapter < args.start:
            continue
        if chapter > last_chapter:
            break
        current_item = driver.find_elements_by_class_name("current")
        for item in current_item:
            if item.tag_name == 'ul':
                chapter_box = item
        chapter_list = chapter_box.find_elements_by_tag_name("li")
        if chapter_list[i].get_attribute("class") in ["pay", "free"]:
            print("You haven't paid for chapter {:d}.".format(chapter))
            continue

        # goto chapter page and scroll to the bottom
        chapter_list[i].find_element_by_tag_name("span").click()
        time.sleep(1)
        img_list = driver.find_element_by_class_name("reader-content").find_elements_by_tag_name("li")
        img_num = len(img_list)
        print("Scrolling down chapter {:d}".format(chapter))
        while True:
            driver.execute_script("window.scrollBy(0,500)")
            html = driver.page_source
            bs = BeautifulSoup(html, "html.parser")
            images = bs.findAll("div", {'style': re.compile('opacity: 1; background-image: url+')})
            if len(images) == img_num - 1:
                break

        # start downloading
        print("Start downloading chapter {:d}".format(chapter))
        while True:
            try:
                try:
                    os.mkdir("{:03d}".format(chapter))
                except:
                    os.removedirs("{:03d}".format(chapter))
                    shutil.rmtree("{:03d}".format(chapter))
                for j, img in enumerate(images):
                    style = img['style']
                    img_url = style[style.find('"')+1:style.rfind('"')]
                    req.urlretrieve(img_url, "{:03d}/{:03d}_{:02d}.jpg".format(chapter,chapter,j+1))
                break
            except:
                print("Chapter {:d} download failed. Start downloading again.".format(chapter))
                shutil.rmtree("{:03d}".format(chapter))

        # back to main page
        driver.get(url)
        time.sleep(1)

        # end program
        if chapter == args.end - 1:
            print("Finish.")
            exit(0)



