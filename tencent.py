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
parser.add_argument('--id', type=str, default='623654')
parser.add_argument('--start', type=int, default=1026)
parser.add_argument('--end', type=int, default=0)
args = parser.parse_args()
url = "https://dm.vip.qq.com/club/client/ipadComic/html/large-scale/comic/detail.html?id="+args.id

def imgdownload(url, filename):
    while True:
        try:
            req.urlretrieve(url, filename)
            file_output = os.popen("ls "+filename).read()
            if file_output == "":
                raise RuntimeError
            else:
                print(file_output.strip() +" download finished.")
            break
        except Exception as e:
            print(e)
            print(filename, "download failed. Try again.")
            time.sleep(1)

def startBrowser():
    # open the website
    driver = webdriver.Chrome()
    driver.get(url)
    time.sleep(5)
    iframe = driver.find_element_by_id("login_frame")

    driver.switch_to.frame(iframe)
    try:
        login_button = driver.find_elements_by_class_name("face")
        if len(login_button) > 1:
            login_button[0].click()
    except:
        pass
    driver.switch_to.parent_frame()
    return driver

driver = startBrowser()

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
    i_try = 0
    while True:
        try:
            time.sleep(1)
            nav = driver.find_elements_by_class_name("swiper-slide")[n]
            break
        except:
            i_try += 1
            if i_try > 3:
                print("Finish.")
                driver.quit()
                exit(0)
            driver.refresh()
            time.sleep(5)
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
        while True:
            try:
                current_item = driver.find_elements_by_class_name("current")
                for item in current_item:
                    if item.tag_name == 'ul':
                        chapter_box = item
                chapter_list = chapter_box.find_elements_by_tag_name("li")
                if len(chapter_list) > 0:
                    break
            except:
                pass
            driver.refresh()
            time.sleep(5)

        if last_chapter is None:
            last_chapter = len(chapter_list)
        # if you are not a SVIP, "free" should also added to the following list like "pay"
        if chapter_list[i].get_attribute("class") in ["pay"]:
            print("You haven't paid for chapter {:d}.".format(chapter))
            continue

        # goto chapter page and scroll to the bottom
        scrollspeed = 600
        thres = 20
        while True:
            try:
                chapter_span = chapter_list[i].find_element_by_tag_name("span")
                chapter_span.click()
                time.sleep(1)
            except:
                pass
            try:
                img_list = driver.find_element_by_class_name("reader-content").find_elements_by_tag_name("li")
                break
            except:
                print("Get image list failed. Try again.")
                driver.refresh()
                time.sleep(1)
        img_num = len(img_list)
        print("Scrolling down chapter {:d}".format(chapter))
        curr_num = 0
        no_update = 0
        sleeptime=0.2
        while True:
            driver.execute_script("window.scrollBy(0, {:d})".format(scrollspeed))
            html = driver.page_source
            bs = BeautifulSoup(html, "html.parser")
            images = bs.findAll("div", {'style': re.compile('opacity: 1; background-image: url+')})
            time.sleep(sleeptime)
            if len(images) == img_num - 1:
                break
            if len(images) == curr_num:
                no_update += 1
            else:
                no_update = 0
                curr_num = len(images)
            if no_update == thres:
                thres = 200
                notloaded = True
                while notloaded:
                    buttons = driver.find_elements_by_class_name("yellow-btn")
                    for button in buttons:
                        if button.text == "重新加载":
                            button.click()
                            time.sleep(1)
                    notloaded = False
                    buttons = driver.find_elements_by_class_name("yellow-btn")
                    for button in buttons:
                        if button.text == "重新加载":
                            notloaded = True
                            driver.refresh()
                            break
                driver.refresh()
                no_update = 0
                thres *= 3
                sleeptime *= 2
                # scrollspeed *= -1
                print("Scroll again.")


        # start downloading
        timeout = 8
        error = False
        success_lst = []
        print("Start downloading chapter {:d}".format(chapter))

        chapter_dir = "{:04d}".format(chapter)
        try:
            os.mkdir(chapter_dir)
        except Exception as e:
            shutil.rmtree(chapter_dir)
            os.mkdir(chapter_dir)
        while True:
            process_list = []
            for j, img in enumerate(images):
                if j in success_lst:
                    continue
                style = img['style']
                img_url = style[style.find('"')+1:style.rfind('"')]
                cut_idx = img_url.rfind(".jpg") + 5
                img_url = img_url[:cut_idx]
                if img_url.endswith("?"):
                    img_url = img_url[:-1]
                fname = "{:04d}/{:04d}_{:02d}.jpg".format(chapter,chapter,j+1)
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
                    print("{:04d}/{:04d}_{:02d}.jpg download time out. Try again.".format(chapter,chapter,j+1))
                else:
                    success_lst.append(j)
            if error and timeout > 15:
                print("Network gets wrong. Restart browser.")
                driver.quit()
                time.sleep(5)
                driver = startBrowser()
                time.sleep(5)
                chapter -= 1
                i -= 1
                break
            timeout += 5
            if not error:
                outputs = os.popen("ls "+chapter_dir).read()
                if len(outputs.split("\n")) != img_num:
                    print("Chapter {:d} download get wrong. Try again".format(chapter))
                    chapter -= 1
                    i -= 1
                    break
            if not error:
                print("Chapter {:d} download finished.".format(chapter))
                break


        # back to main page
        driver.get(url)
        time.sleep(1)

        # end program
        if chapter == args.end - 1:
            print("Finish.")
            driver.quit()
            exit(0)
