from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import UnexpectedAlertPresentException
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
import time
from datetime import datetime, timedelta
import os
from Scheduler import Scheduler
import config

BOT_TOKEN = config.BOT_TOKEN

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
options = webdriver.ChromeOptions()
path = r'C:\Users\bitle\Downloads\chromedriver_win32\chromedriver.exe'
#path = '/usr/local/share/chromedriver'
#options.add_argument('headless')
#options.add_argument("--no-sandbox")
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
options.add_argument(f'user-agent={user_agent}')

class Scanner():
    driver = None
    notifier = None
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=path, chrome_options=options)
    
    def removePopup(self):
        _tabs = self.driver.window_handles
        while len(_tabs) != 1:
            self.driver.switch_to.window(_tabs[1])
            self.driver.close()
            _tabs = self.driver.window_handles
        self.driver.switch_to.window(_tabs[0])

    def login(self):
        url = "https://www.cgv.co.kr/user/login/?returnURL=https%3a%2f%2fwww.cgv.co.kr%2fdefault.aspx"
        self.driver.get(url)
        wait(self.driver, 3).until(lambda d: d.find_element(By.ID, "txtUserId")).send_keys(config.cgvid)
        self.driver.find_element(By.ID, "txtPassword").send_keys(config.cgvpassword + Keys.ENTER)

    def scanDate(self, date):
        found = False
        url = "http://www.cgv.co.kr/theaters/?theatercode=0013&areacode=01&date=" + date
        self.driver.get(url)
        frame = wait(self.driver, 3).until(lambda d: d.find_element(By.ID, "ifrm_movie_time_table"))
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

    def openReservationPage(self, url):
        if url:
            self.driver.get(url)
        frame = wait(self.driver, 3).until(lambda d: d.find_element(By.ID, "ticket_iframe"))
        self.driver.switch_to.frame(self.driver.find_element(By.CSS_SELECTOR, ("iframe#ticket_iframe")))
        next_button = wait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, "tnb_step_btn_right")))
        while next_button.get_attribute("className") != "btn-right on":
            time.sleep(0.5)
        # class="dimm" 로딩 아이콘에 클릭 막힘
        time.sleep(1)
        next_button.click()
        blocking = wait(self.driver, 5).until(lambda d: d.find_element(By.ID, "blackscreen"))
        time.sleep(1)
        self.driver.execute_script('document.getElementById("blackscreen").style["display"]="None";')

    def findCancelSeat(self, n, row=(6, 12)):
        """
        Scan seats and if there is open seats for the given section, it fires alarm to user.
        Supposed to be executed after @openReservationPage()

        Args:
            n (int): number of ticket to be reserved
            row (tuple): rows to see if there are seats. Default section is F-L(inclusive, 1-indexed)

        Returns:
            None
        """ 
        try:
            wait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#ticket > div.steps > div.step.step2 > a"))).send_keys(Keys.ENTER)
            seats_available = []
            #row = (3, 5)
            col = (16, 29)
            wait(self.driver, 5).until(lambda d: d.find_element(By.CSS_SELECTOR, f"#nop_group_adult > ul > li:nth-child({n + 1})")).click()
        except UnexpectedAlertPresentException as e:
            next_button = wait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, "tnb_step_btn_right")))
            while next_button.get_attribute("className") != "btn-right on":
                time.sleep(0.5)
            # class="dimm" 로딩 아이콘에 클릭 막힘
            time.sleep(1)
            next_button.click()
            blocking = wait(self.driver, 5).until(lambda d: d.find_element(By.ID, "blackscreen"))
            time.sleep(1)
            self.driver.execute_script('document.getElementById("blackscreen").style["display"]="None";')
        rows = []
        for i in range(row[0], min(row[1], 9)):
            rows.append(self.driver.find_element(By.CSS_SELECTOR, f"#seats_list > div:nth-child(1) > div:nth-child({i}) > div:nth-child(4)"))
        for i in range(9, row[1] + 1):
            rows.append(self.driver.find_element(By.CSS_SELECTOR, f"#seats_list > div:nth-child(1) > div:nth-child({i}) > div:nth-child(5)"))

        for i in range(len(rows)):
            seat_list = rows[i].get_attribute("innerText").split("\n")
            pointer = 0
            while pointer < len(seat_list):
                #print(chr(ord('A') + i), seat_list[pointer])
                if seat_list[pointer].isnumeric():
                    if pointer + 1 == len(seat_list) or seat_list[pointer + 1].isnumeric():
                        seats_available.append((chr(ord('A') + row[0] - 1 + i), seat_list[pointer]))
                pointer += 1
        
        if seats_available:
            info_movie = self.driver.find_element(By.CSS_SELECTOR, "#ticket_tnb > div > div.info.movie").get_attribute("innerText")
            info_theater = self.driver.find_element(By.CSS_SELECTOR, "#ticket_tnb > div > div.info.theater").get_attribute("innerText").split("\n")
            info_theater = "\n".join(info_theater[1::2])
            info_seat = " ".join(["".join(seat) for seat in seats_available])

            message = f"예약 가능한 자리 알림\n\n{info_movie}\n\n{info_theater}\n\n{info_seat}"
            updater.bot.send_message(5794019445, message)
            print(f"@findCancelSeat - seats found and message has been sent\n{message}")
        else:
            print(f"@findCancelSeat - no seats open for rows {row[0]} to {row[1]} at {datetime.now()}")
        return seats_available

if __name__ == "__main__":
    scanner = Scanner()
    sc = Scheduler()
    scanner.login()
    scanner.openReservationPage("http://www.cgv.co.kr/ticket/?MOVIE_CD=20030777&MOVIE_CD_GROUP=20023836&PLAY_YMD=20221015&THEATER_CD=0013&PLAY_START_TM=1345&AREA_CD=13&SCREEN_CD=018")
    #scanner.findCancelSeat(2)
    #sc.setup_scanning(scanner.scanDate, [date], 60, datetime.now(), "imax finder")
    sc.setup_scanning(scanner.findCancelSeat, [2], 60, datetime.now(), "seat finder tenet")
    while True:
        pass