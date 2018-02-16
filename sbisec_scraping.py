#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""a stock order via SBI Securities.

    "order_sbisec.py" is released under the MIT License
    Copyright (c) 2017 Akihiro Yamamoto
__author__  = "Akihiro Yamamoto <ak1211@mail.ak1211.com>"
__version__ = "0.5.2"
__date__    = "Oct 2017"
"""

from abc import ABCMeta
from time import sleep

import lxml.html
import requests

import traceback
import yaml

WAITING_TIME = 0.3


class Securities (metaclass=ABCMeta):
    """A securities provider."""

    def login(self):
        """Login the website."""
        pass

    def get_top_page(self):
        """Get top page on website."""
        pass

    def logout(self):
        """Logout the website."""
        pass

    def portfolio_assets(self):
        """My portfolio."""
        pass

    def stocks_sell_order(self, code, quantity, price):
        """Sell order."""
        pass


class SBISecurities(Securities):
    """SBI securities provider."""

    def __init__(self, uid, upass, tpass, userAgent):
        """Init this instance."""
        self.userID = uid
        self.userPassword = upass
        self.tradePassword = tpass
        self.defHeaders = {
            'Accept': 'text/html',
            'User-agent': userAgent
        }
        self.session = requests.session()
        self.siteRoot = None

    def login(self):
        """Login the website."""
        def the_first_post(htmltext):
            custom = {
                'JS_FLG': '1',
                'BW_FLG': 'chrome,56',
                'ACT_login.x': '39',
                'ACT_login.y': '26',
                'user_id': self.userID,
                'user_password': self.userPassword
            }
            # htmlのルート要素
            root = lxml.html.fromstring(htmltext)
            form_inputs = root.xpath('//form[@name="form_login"]//input')
            # ログインフォームのinput要素
            inputs = {x.get('name'): x.get('value') for x in form_inputs}
            # ログイン情報を用意する
            del inputs['ACT_login']
            inputs.update(custom)
            # ログイン情報を送信する(postで)
            sleep(WAITING_TIME)
            r = self.session.post('https://www.sbisec.co.jp/ETGate',
                                  data=inputs, headers=self.defHeaders)
            return r

        def the_second_post(htmltext):
            # 受け取ったページのformSwitchフォームを取り出す
            root = lxml.html.fromstring(htmltext)
            form = root.xpath('//form[@name="formSwitch"]')
            form_attribute = form[0].attrib
            form_inputs = root.xpath('//form[@name="formSwitch"]//input')
            inputs = {x.get('name'): x.get('value') for x in form_inputs}
            # formSwitchフォームの内容をそのまま送信する
            act = form_attribute.get('action')
            sleep(WAITING_TIME)
            r = self.session.post(act, data=inputs, headers=self.defHeaders)
            return r
        #
        # ログイン
        r = self.session.get('https://www.sbisec.co.jp/ETGate',
                             headers=self.defHeaders)
        if r.status_code == requests.codes.ok:
            r = the_first_post(r.text)
            if r.status_code == requests.codes.ok:
                r = the_second_post(r.text)
                if r.status_code == requests.codes.ok:
                    r.encoding = r.apparent_encoding
                    self.siteRoot = lxml.html.fromstring(r.text)
        return r

    def get_top_page(self):
        """Get top page on website."""
        return self.siteRoot

    def logout(self):
        """Logout the website."""
        # a要素の子要素でalt属性が"ログアウト"のページを得る
        return self._request_at_GET_method(self.siteRoot,
                                           '//a[*[contains (@alt,"ログアウト")]]')

    def fetch_portfolio_page(self):
        """Fetch a 'portfolio' page on website."""
        # a要素の子要素でalt属性が"ポートフォリオ"のページを得る
        return self._request_at_GET_method(self.siteRoot,
                                           '//a[*[contains(@alt,"ポートフォリオ")]]')

    def portfolio_assets(self):
        """My portfolio."""
        # a要素の子要素でalt属性が"口座管理"のページを得る
        xdoc = self._request_at_GET_method(self.siteRoot,
                                           '//a[*[contains(@alt,"口座管理")]]')
        return self._request_at_GET_method(xdoc, '//area[@title="保有証券"]')

    def stocks_sell_order(self, code, quantity, price):
        """Sell order."""
        orderFormInputs = {
            # "取引" ラジオボタン
            # 0 -> 現物買
            # 1 -> 現物売
            # 2 -> 信用新規買
            # 3 -> 信用新規売
            'trade_kbn': '1',
            # 銘柄コード
            'stock_sec_code': code,
            # "市場" セレクトボックス
            # "   " -> 当社優先市場／SOR
            # "TKY" -> 東証
            # "NGY" -> 名証
            # "FKO" -> 福証
            # "SPR" -> 札証
            'input_market': '   ',
            # 株数
            'input_quantity': quantity,
            # "価格" ラジオボタン
            # " " -> 指値
            # "N" -> 成行
            # "G" -> 逆指値
            'in_sasinari_kbn': ' ',
            #
            # 指値の"条件" セレクトボックス
            #
            # " " -> 条件なし
            # "Z" -> 寄指(Y)
            # "I" -> 引指(H)
            # "F" -> 不成(F)
            # "P" -> IOC指(I)
            'sasine_condition': ' ',
            #
            # 成行の"条件" セレクトボックス
            #
            # "N" -> 条件なし
            # "Y" -> 寄成(Y)
            # "H" -> 引成(H)
            # "O" -> IOC成(I)
            'nariyuki_condition': 'N',
            #
            # 逆指値
            #
            # 現在値が
            'input_trigger_price': '',   # 円
            # "以上" "以下" セレクトボックス
            # "0" -> 以上
            # "1" -> 以下
            'input_trigger_zone': 1,    # になった時点で
            # 逆指値の"指値" "成行" ラジオボタン
            # " " -> 指値
            # "N" -> 成行
            'gsn_sasinari_kbn': ' ',
            #
            # 逆指値の"指値" 条件セレクトボックス
            # " " -> 条件なし
            # "I" -> 引指(H)
            # "F" -> 不成(F)
            'gsn_sasine_condition': ' ',
            # 逆指値の"指値" 値段:
            'gsn_input_price': '',   # 円で執行
            #
            # 逆指値の"成行" 条件セレクトボックス
            # "N" -> 条件なし
            # "H" -> 引成(H)
            'gsn_nariyuki_condition': 'N',  # で執行
            #
            # 値段
            'input_price': price,
            # 期間
            # "this_day" -> 当日中
            # "kikan" -> 期間指定
            'selected_limit_in': 'this_day',
            # 預り区分
            # "1" -> 一般預り
            # "0" -> 特定預り
            'hitokutei_trade_kbn': '0',
            # 信用取引区分
            # "6" -> 制度
            # "9" -> 一般
            # "D" -> 日計り
            'payment_limit': '6',
            # 取引パスワード
            'trade_pwd': self.tradePassword,
            # 注文確認画面を省略
            'skip_estimate': 'on',
            # 注文発注
            'ACT_place': '注文発注'
        }
        return self._stocks_buy_or_sell_order(orderFormInputs)

    def _stocks_buy_or_sell_order(self, formInputs):
        """Buy or sell order."""
        # a要素の子要素でalt属性が"取引"のページを得る
        root = self._request_at_GET_method(self.siteRoot,
                                           '//a[*[contains(@alt,"取引")]]')
        # フォームのinput要素
        inputs = {x.get('name'): x.get('value')
                  for x in root.xpath('//form[@name="FORM"]//input')}
        # 期間指定セレクトボックスのoption
        limit_in_options = root.xpath('//select[@name="limit_in"]//option')
        options = map(lambda x: x.get('value'), limit_in_options)
        # 入力情報を用意する
        # 期間指定セレクトボックスのoptionはとりあえず先頭の物を選択する
        inputs["limit_in"] = list(options)[0]
        del inputs['ACT_estimate']
        del inputs['ACT_order']
        del inputs[None]
        inputs.update(formInputs)
        # 注文情報を送信する(postで)
        sleep(WAITING_TIME)
        r = self.session.post('https://site2.sbisec.co.jp/ETGate',
                              data=inputs, headers=self.defHeaders)
        r.encoding = r.apparent_encoding
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        return lxml.html.fromstring(r.text)

    def _request_at_GET_method(self, xdoc, xp):
        """Request on website."""
        # リンクを取り出す
        form = xdoc.xpath(xp)
        link = 'https://site2.sbisec.co.jp' + form[0].get('href')
        sleep(WAITING_TIME)
        r = self.session.get(link, headers=self.defHeaders)
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        r.encoding = r.apparent_encoding
        return lxml.html.fromstring(r.text)


if __name__ == '__main__':
    def row2list(tr):
        """<td>text</td> to list."""
        tds = list(tr)
        return [w.text_content().replace(u'\xa0', ' ').strip() for w in tds]

    f = open("sbisec_scraping.yaml", "r+")
    conf = yaml.load(f)
    f.close()

    sec = SBISecurities(conf['user_name'],
                        conf['password'],
                        conf['trade_password'],
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/56.0.2924.87 Safari/537.36')

    r = sec.login()
    if r.status_code == requests.codes.ok:
        try:
            #
            #print('ログイン後のホームページ')
            tp = sec.get_top_page()
            #contents = tp.xpath('//form/table[3]/tr/td/table/tr')
            #w = list(map(row2list, contents))
            #print(w)
            # "ポートフォリオ"ページ
            print('ポートフォリオ"ページ')
            funds = {}
            pf = sec.fetch_portfolio_page()
            trs = pf.xpath('/html/body/div[3]/div'
                           '/table/tr/td/table[4]/tr[2]/td/table/tr')
            matrix = list(map(row2list, trs))
            trs = pf.xpath('/html/body/div[3]/div'
                           '/table/tr/td/table[4]/tr[6]/td/table/tr')
            matrix += list(map(row2list, trs))
            for f in matrix:
                if f[0] != '取引':
                    funds[f[1]] = funds.get(f[1], 0) + int(f[10].replace(",", "").split(".")[0])
            total = sum(funds.values())
            for k, v in funds.items():
                print(v * 100 / total, k)
            # 保有証券資産
            #print('保有証券資産')
            #myStocks = sec.portfolio_assets()
            #trs = myStocks.xpath('//form/table[2]/tr[1]/td[2]'
            #                     '/table[6]/tr/td/table/tr')
            #tr = list(map(row2list, trs))
            #print(tr)
            # 注文
            #print('注文')
            #so = sec.stocks_sell_order(4689, 100, 500)
            #w = so.xpath('/html/body/div/table/*')
            #print(w[0].text_content().split())
        except requests.HTTPError:
            print('失敗しました。')
            print(traceback.format_exc())
        finally:
            # ログアウト
            print('ログアウト')
            root = sec.logout()
            m = root.xpath('string(//div[@class="alC"]/.)')
            print(m.split())
