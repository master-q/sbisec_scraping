import yaml

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class SbiSec:

        def __init__(self, conf):
                self.driver = webdriver.Chrome("/usr/bin/chromedriver")
                self.user_id = conf["user_id"]
                self.user_password = conf["user_password"]

        def get_portfolio(self):
                driver = self.driver
                driver.get("https://www.sbisec.co.jp/ETGate")

                driver.find_element_by_name("user_id").send_keys(self.user_id)
                driver.find_element_by_name("user_password").send_keys(self.user_password)
                driver.find_element_by_name("ACT_login").click()

                driver.get("https://site2.sbisec.co.jp/ETGate/?_ControlID=WPLETpfR001Control&_PageID=DefaultPID&_DataStoreID=DSWPLETpfR001Control&_ActionID=DefaultAID&getFlg=on")
                elements = driver.find_elements_by_class_name("mtext")
                print(type(elements))
                for i in elements:
                        print(i.text)

        def __del__(self):
                self.driver.close()

if __name__ == "__main__":
        f = open("sbisec_scraping.yaml", "r+")
        conf = yaml.load(f)
        f.close()
        print(type(conf))

        sbisec = SbiSec(conf)
        sbisec.get_portfolio()
        del sbisec
