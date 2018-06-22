from selenium import webdriver
import argparse
import time
import urllib.request as req
import re
import shutil
import os
from bs4 import BeautifulSoup
from multiprocessing import Process

parser = argparse.ArgumentParser(description='Tecent comic download.')
parser.add_argument('--id', type=str, default='626438')
parser.add_argument('--start', type=int, default=1)
parser.add_argument('--end', type=int, default=0)
args = parser.parse_args()
url = "https://dm.vip.qq.com/club/client/ipadComic/html/large-scale/comic/detail.html?id="+args.id

def imgdownload(url, filename):
    while True:
        try:
            req.urlretrieve(url, filename)
            break
        except:
            print(filename, "download failed. Try again.")

# open the website
driver = webdriver.Chrome()
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
        time.sleep(1)
        nav = driver.find_elements_by_class_name("swiper-slide")[n]
    except:
        print("Finish.")
        exit(0)
    if nav.tag_name != "li":
        continue
    try:
        nav.click()
        first_chapter = int(nav.text.split('-')[0])
        last_chapter = int(nav.text.split('-')[1])
    except:
        first_chapter = 1
        last_chapter = None

    i = -1
    while True:
        i += 1
        chapter = first_chapter + i
        if chapter < args.start:
            continue
        if last_chapter is not None and chapter > last_chapter:
            break
        time.sleep(1)
        current_item = driver.find_elements_by_class_name("current")
        for item in current_item:
            if item.tag_name == 'ul':
                chapter_box = item
        chapter_list = chapter_box.find_elements_by_tag_name("li")
        if last_chapter is None:
            last_chapter = len(chapter_list)
        if chapter_list[i].get_attribute("class") in ["pay", "free"]:
            print("You haven't paid for chapter {:d}.".format(chapter))
            continue

        # goto chapter page and scroll to the bottom
        scrollspeed = 60
        thres = 200
        chapter_span = chapter_list[i].find_element_by_tag_name("span")
        chapter_span.click()
        time.sleep(1)
        while True:
            try:
                img_list = driver.find_element_by_class_name("reader-content").find_elements_by_tag_name("li")
                break
            except:
                print("Get image list failed.")
                time.sleep(1)
        img_num = len(img_list)
        print("Scrolling down chapter {:d}".format(chapter))
        curr_num = 0
        no_update = 0
        while True:
            driver.execute_script("window.scrollBy(0, {:d})".format(scrollspeed))
            html = driver.page_source
            bs = BeautifulSoup(html, "html.parser")
            images = bs.findAll("div", {'style': re.compile('opacity: 1; background-image: url+')})
            if len(images) == img_num - 1:
                break
            if len(images) == curr_num:
                no_update += 1
            else:
                no_update = 0
                curr_num = len(images)
            if no_update == thres:
                no_update = 0
                thres *= 3
                scrollspeed //= -2
                print("Scroll again.")


        # start downloading
        timeout = 8
        error = False
        success_lst = []
        print("Start downloading chapter {:d}".format(chapter))
        while True:
            process_list = []
            if not error:
                try:
                    os.mkdir("{:03d}".format(chapter))
                except:
                    os.removedirs("{:03d}".format(chapter))
                    shutil.rmtree("{:03d}".format(chapter))
            for j, img in enumerate(images):
                if j in success_lst:
                    continue
                style = img['style']
                img_url = style[style.find('"')+1:style.rfind('"')]
                fname = "{:03d}/{:03d}_{:02d}.jpg".format(chapter,chapter,j+1)
                p = Process(target=imgdownload, args=(img_url, fname))
                p.daemon = True
                p.start()
                process_list.append(p)
            error = False
            timeout_ = timeout
            for j, p in enumerate(process_list):
                p.join(timeout_)
                if p.is_alive():
                    p.terminate()
                    error = True
                    timeout_ = 1
                    print("{:03d}/{:03d}_{:02d}.jpg download time out. Try again.".format(chapter,chapter,j+1))
                else:
                    success_lst.append(j)
            if not error:
                break

        print("Chapter {:d} download finished.".format(chapter))

        # back to main page
        driver.get(url)
        time.sleep(1)

        # end program
        if chapter == args.end - 1:
            print("Finish.")
            exit(0)
