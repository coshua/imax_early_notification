from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import time
from datetime import datetime, timedelta
import os
from Scheduler import Scheduler

BOT_TOKEN = "5792832504:AAEvFuVtYKEUrjMvLnpGMnzd1vr5OqdCMnE"

# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logger = logging.getLogger(__name__)
bot = Bot(BOT_TOKEN)
def echo(update: Update, context:CallbackContext):
    update.message.reply_text(update.message.text)

updater = Updater(BOT_TOKEN)
# updater.bot.send_message(5794019445, "This is bot")
dispatcher = updater.dispatcher
#dispatcher.add_handler(MessageHandler(Filters.text, echo))
# updater.start_polling()
# updater.idle()
path = r'C:\Users\bitle\Downloads\chromedriver_win32\chromedriver.exe'
options = webdriver.ChromeOptions()
options.add_argument('headless')
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
options.add_argument(f'user-agent={user_agent}')
# options.add_argument("--no-sandbox")
class Scanner():
    driver = None
    notifier = None
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=path, chrome_options=options)

    def scanDate(self, date):
        found = False
        url = "http://www.cgv.co.kr/theaters/?theatercode=0013&areacode=01&date=" + date
        self.driver.get(url)
        # self.driver.save_screenshot('iframe.png')
        # body = self.driver.find_element(By.ID, "cgvwrap")
        # ht = body.size["height"]+1000
        # self.driver.set_window_size(1920, ht)
        # time.sleep(1)
        # self.driver.save_screenshot("test.png")
        # body.screenshot('test2.png')
        #self.save_screenshot(self.driver)
        frame = wait(self.driver, 3).until(lambda d: d.find_element(By.ID, "ifrm_movie_time_table"))
        #body = self.driver.find_element(By.CSS_SELECTOR, ("iframe#ifrm_movie_time_table > html > body"))
        #frame.screenshot('test.png')
        self.driver.switch_to.frame(self.driver.find_element(By.CSS_SELECTOR, ("iframe#ifrm_movie_time_table")))
        #wait(self.driver, 3).until(lambda d: d.find_element(By.CSS_SELECTOR, (".col-times")))
        movie_list = self.driver.find_elements(By.CSS_SELECTOR, (".col-times"))
        #movie_list = self.driver.find_elements(By.CSS_SELECTOR, ("iframe#ifrm_movie_time_table > html > body > div.showtimes-wrap > div.sect-showtimes > ul > li"))
        for i in range(len(movie_list)):
            infotxt = movie_list[i].get_attribute("innerText")
            if infotxt.find('IMAX') > -1:
                messages = []
                movie_info = infotxt.split("\n")
                movie_title = movie_info[1].split(" ")[0]
                content = self.driver.find_elements(By.CSS_SELECTOR, (f"div.sect-showtimes > ul > li:nth-child({i + 1}) > div.col-times > div.type-hall > div.info-timetable > ul > li > a"))
                for i in range(len(content)):
                    # find out if seats are available or pending
                    # 12:25\n300석 or 12:25\n준비중
                    isPending = content[i].get_attribute("innerText")
                    if isPending[1] == "준비중":
                        start_time = isPending[0]
                        messages.append(f"{movie_title}\n{start_time} 예매준비중")
                    else:
                        date = content[i].get_attribute("data-playymd")
                        start_time = content[i].get_attribute("data-playstarttime")
                        cnt_seat = content[i].get_attribute("data-seatremaincnt")
                        messages.append(f"{movie_title} {date} {start_time}\n남은 좌석: {cnt_seat}")
                print(f"@scanDate - IMAX {movie_title} is about to open! {date}\n")
                updater.bot.send_message(5794019445, "\n".join(messages))
                found = True
        if not found:
            print(f"@scanDate - IMAX is not yet opened {date}")
        return found
        # self.driver.switch_to.default_content()
if __name__ == "__main__":
    scanner = Scanner()
    sc = Scheduler()
    date = "20221012"
    sc.setup_scanning(scanner.scanDate, [date], 60, datetime.now(), "imax finder")
    while True:
        pass