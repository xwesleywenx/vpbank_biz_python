
import hashlib
import json
import base64
import random
import string
import base64
import json
import os
import hashlib
import time
import uuid
import base64
from datetime import datetime
import re
from bs4 import BeautifulSoup
from lxml import html
import urllib.parse
from bypass_ssl_v3 import get_legacy_session
from urllib.parse import quote
import requests

# requests = get_legacy_session()
class VPB:
    def __init__(self, username, password, account_number):
        # setting proxy
        with open('proxies.txt', 'r') as file:
            proxy_list = [line.strip() for line in file if line.strip()]
        proxy_list = proxy_list if proxy_list else None
        self.proxy_list = proxy_list
        if self.proxy_list:
            self.proxy_info = random.choice(self.proxy_list)
            proxy_host, proxy_port, username_proxy, password_proxy = self.proxy_info.split(':')
            self.proxies = {
                'http': f'http://{username_proxy}:{password_proxy}@{proxy_host}:{proxy_port}',
            }
        else:
            self.proxies = None

        self.session = get_legacy_session()
        self.is_login = False
        self.file = f'data/{username}.txt'
        self.cookie = ''
        self.url = {
            "login_page":"https://online.vpbank.com.vn/neobiz/login",
            "getCaptcha": "https://online.vpbank.com.vn/neobiz/JpegImage.aspx",
            "login": "https://online.vpbank.com.vn/neobiz/AjaxService/Services.aspx",
            "get_balance": "https://online.vpbank.com.vn/neobiz/default",
            "setHistoriesConditions":"https://online.vpbank.com.vn/neobiz/modules/tracuu/GetAccStmt.aspx?",
            "getHistories": "https://online.vpbank.com.vn/neobiz/acstmt",
        }

        self.retry_login = 0
        self.retry_captcha = 0
        self.retry_balance = 0
        self.retry_keepalive = 0
        self.retry_transactions = 0
        if not os.path.exists(self.file):
            self.username = username
            self.password = password
            self.account_number = account_number
            self.cookie = None
            self.save_data()
        else:
            self.parse_data()
            self.username = username
            self.password = password
            self.account_number = account_number

    def save_data(self):
        data = {
            'username': self.username,
            'password': self.password,
            'account_number': self.account_number,
            'cookie': getattr(self, 'cookie', ''),
        }
        with open(self.file, 'w') as f:
            json.dump(data, f)

    def parse_data(self):
        with open(self.file, 'r') as f:
            data = json.load(f)
        self.username = data.get('username', '')
        self.password = data.get('password', '')
        self.account_number = data.get('account_number', '')
        self.cookie = data.get('cookie', '')
        
    
    def curlGet(self, url, headers = None, allow_redirects = False):
        # print('curlGet')
        if not headers:
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': self.cookie,
                'Origin': 'https://online.vpbank.com.vn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0'
            }

        response = self.session.get(url, headers=headers, proxies=self.proxies, allow_redirects=allow_redirects)
        try:
            return response.json()
        except:
            response = response.text
            return response
    
    def curlPost(self, url, data, headers = None):
        # print('curlPost')
        if not headers:
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': self.cookie,
                'Origin': 'https://online.vpbank.com.vn',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
                'X-requested-with':'XMLHttpRequest'
            }

        response = self.session.post(url, headers=headers, data=data, proxies=self.proxies)
        try:
            return response.json()
        except:
            response = response.text
            return response
    
    def extract_by_pattern(self,html_content,pattern):
        match = re.search(pattern, html_content)
        return match.group(1) if match else None
    
    def identifyCaptcha(self, image):
        payload = {
            'image': image,
            'model': 'vpbbiz'
        }
        headers = {
            'Content-Type':'application/json'
        }
        response = requests.post("http://localhost:19952/captcha/v1", data=json.dumps(payload), headers=headers)
        if response is not None:
            return response.json()
        else:
            return {}

    def solveCaptcha(self):
        url = self.url['getCaptcha']
        for _ in range(3):  # 最多重试三次
            url = url + "?rnd" + str(random.random())
            captcha_headers = {
                        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br, zstd',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0'
            }
            response = self.session.get(url, headers=captcha_headers)
            
            # 图片转base64
            base64_captcha_img = base64.b64encode(response.content).decode("utf-8")

            result = self.identifyCaptcha(base64_captcha_img)
            
            if 'message' in result and result['message']:
                if len(result['message']) == 6:
                    captcha_value = result['message']
                    return {"status": True, "captcha": captcha_value}
                else:
                    continue  # 重试
            else:
                return {"status": False, "msg": "Error solving captcha", "data": result}

        return {"status": False, "msg": "Error solving captcha", "data": "captcha retry over three times"}
    
    def doLogin(self):
        # self.session = get_legacy_session()

        # 把语言转为英文
        login_page_headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://online.vpbank.com.vn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'X-requested-with':'XMLHttpRequest'
        }
        response = self.curlPost(self.url["login_page"], headers=login_page_headers, data="lang=en")

        solveCaptcha = self.solveCaptcha()
        if not solveCaptcha["status"]:
            print(f'Unknown Error! 【captcha】')
            return {
                    'code': 520,
                    'success': False,
                    'message': "Unknown Error!"
            }
            # return solveCaptcha
        captcha_text = solveCaptcha["captcha"]
        json_data = {"UserName":self.username, "Password":self.password, "Capcha":captcha_text, "lastLoginID":""}
        # 使用 json.dumps() 将字典转换为字符串
        json_string = json.dumps(json_data)
        payload = 'func='+quote('login')+'&jsonData='+quote(json_string)
        login_headers = {
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://online.vpbank.com.vn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'X-requested-with':'XMLHttpRequest'
        }
        self.retry_login += 1
        response = self.curlPost(self.url["login"], payload,login_headers)
        print(response)
        if "IsSuccess" in response and response["IsSuccess"] == 1:
            # 获取当前会话的 cookies
            cookies_jar = self.session.cookies
            # 将 cookies 转换为字典
            cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
            # 将字典转换为字符串（格式：key=value; key=value; ...）
            self.cookie = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
            self.retry_login = 0
            self.is_login = True
            self.save_data()
            return {
                'code': 200,
                'success': True,
                'message': 'Đăng nhập thành công',
                'data':{
                    'lastLoginID':response["LastLoginID"] 
                }
            }
        else:
            if response['Errors']:
                if 'loginError' in response['Errors'] and 'Login failed' in response['Errors']['loginError']:
                    # 'Đăng nhập không thành công.'
                    return {
                        'code': 404,
                        'success': False,
                        'message': 'Tài khoản không tồn tại hoặc không hợp lệ.',
                    }
                elif 'loginError' in response['Errors'] and 'Incorrect user information or password' in response['Errors']['loginError']:
                    # 'Tên đăng nhập hoặc mật khẩu không chính xác.'
                    return {
                        'code': 444,
                        'success': False,
                        'message': 'Tài khoản hoặc mật khẩu không đúng',
                    }
                elif 'loginError' in response['Errors'] and 'Invalid security number' in response['Errors']['loginError']:
                    # 'Captcha không chính xác'
                    if self.retry_login < 3:
                        self.doLogin()
                    else:
                        return {
                            'code': 422,
                            'success': False,
                            'message': 'Mã Tiếp tục không hợp lệ',
                            }
                elif 'loginError' in response['Errors'] and 'Your account has been locked' in response['Errors']['loginError']:
                    # 'Tài khoản của quý khách đã bị khóa'
                    return {
                        'code': 449,
                        'success': False,
                        'message': 'Blocked account!'                    
                    }
                else:
                    errors_str = json.dumps(response['Errors'])
                    print(f'do login Unknown Error! 【{errors_str}】')
                    return {
                            'code': 520,
                            'success': False,
                            'message': "Unknown Error!"
                    }
            else:
                print(f'do login Unknown Error!')
                return {
                        'code': 520,
                        'success': False,
                        'message': "Unknown Error!"
                }

    def get_balance(self, need_login = False):
        if need_login:
            login = self.doLogin()
            if not login['success']:
                return login

        account_list_headers = {
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': self.cookie,
            'Origin': 'https://online.vpbank.com.vn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'X-requested-with':'XMLHttpRequest'
        }
        self.retry_balance += 1
        account_list_response = self.curlGet(self.url["get_balance"], headers=account_list_headers, allow_redirects=True)
        # session time out 或查询中错误
        error_messages = [
            'Bạn đã hết phiên làm việc! Vui lòng đăng nhập lại.',
            'Có lỗi trong quá trình vấn tin tài khoản, xin vui lòng thử lại !'
        ]
        
        if self.account_number in account_list_response:
            soup = BeautifulSoup(account_list_response, 'html.parser')

            # 找到指定的 <table>
            account_list_table = soup.find('table', {'id': 'ctl00_mainContainer_gridAcList'})
            # 提取表头（即 <th>）
            # Header: ['Index_#', 'Account_No.', 'Account_Currency', 'Ledger_Balance', 'Available_Balance', 'Open_Date', 'Open_Branch', '#']
            account_list_header = [th.get_text().replace(" ", "_") for th in account_list_table.find_all('th')]
           # 根據表頭找到 "account" 的索引
            account_index = account_list_header.index('Account_No.')
            # 根據表頭找到 "Available Balance" 的索引
            available_balance_index = account_list_header.index('Available_Balance')

            # 遍历所有的行，查找帐号
            for row in account_list_table.find_all('tr')[1:]:  # 跳过表头
                cols = row.find_all('td')
                account = cols[account_index].get_text()
                if account == self.account_number:
                    amount = cols[available_balance_index].get_text()  # 提取可用余额
                    print(f"account [{self.account_number}] available balance: {amount}")
                    balance = float(amount.replace(',',''))
                    if balance < 0:
                        return {
                            'code':448,'success': False, 'message': 'Blocked account with negative balances!',
                            'data': {
                                'balance':balance
                            }
                        }
                    else:
                        return {
                            'code':200,'success': True, 'message': 'Thành công',
                            'data':{
                                'account_number':self.account_number,
                                'balance':balance
                            }
                        }
            return {'code':404,'success': False, 'message': 'account_number not found!'}
        elif 'Mật khẩu:' in account_list_response or 'Password:' in account_list_response or '<h2>Object moved to <a href="/neobiz/login">here</a>.</h2>' in account_list_response:
            if self.retry_balance < 3:
                # session time out 或查询中错误 重新登入
                print('get_balance 重新登入')
                self.is_login = False
                return self.get_balance(True)
            else:
                print('balance 查询失败次数过多(retry_balance: ' + self.retry_balance + ') return Unknown Error')
                return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        elif "Do you want to continue working on the system ?" in account_list_response:
            keep_alive_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0'
            }
            self.retry_keepalive += 1
            keep_alive_payload = "func=KeepAlive&jsonData=1"
            print("vpb biz excuting keep alive")
            keep_alive_response = self.curlPost(self.url["login"], data=keep_alive_payload, headers=keep_alive_headers)
            # response text为空才是成功
            if keep_alive_response == '':
                print("vpb biz keep alive sucess")
                # 获取当前会话的 cookies
                cookies_jar = self.session.cookies
                # 将 cookies 转换为字典
                cookies_dict = requests.utils.dict_from_cookiejar(cookies_jar)
                # 将字典转换为字符串（格式：key=value; key=value; ...）
                self.cookie = '; '.join([f'{key}={value}' for key, value in cookies_dict.items()])
                self.save_data()
                if self.retry_keepalive < 2:
                    print('get_balance keep alive 后重新查询')
                    return self.get_balance()
                else:
                    # session time out 或查询中错误 重新登入
                    print('balance keep alive失败次数过多(retry_keepalive: ' + self.retry_keepalive + ') 重新登入')
                    self.is_login = False
                    return self.get_balance(True)
            else:
                print("vpb biz keep alive fail")
                if self.retry_balance < 3:
                    # session time out 或查询中错误 重新登入
                    print('get_balance 重新登入')
                    self.is_login = False
                    return self.get_balance(True)
                else:
                    print('balance 查询失败次数过多(retry_balance: ' + self.retry_balance + ') return Unknown Error')
                    return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        else: 
            print('get balance Unknown Error!')
            print("balance response: " + account_list_response)
            with open('getBalanceError.html', 'w', encoding='utf-8') as file:
                file.write(account_list_response)
            
            return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
    

    def getHistories(self, account_number='',limit = 100, from_date='', to_date='', need_login = False):
        if need_login:
            login = self.doLogin()
            if not login['success']:
                return login
        
        # 设定交易条件
        payload = 'Upgrade='+quote('true')+'&acID='+quote(account_number)+'&fdate='+quote(from_date)+'&tdate='+quote(to_date)+'&famount=&tamount=&memo=&bankid=&fhour='+quote("00:00")+'&thour='+quote("23:59")+'&kindStatement='+quote("0")   
        print("history condition payload: " + payload)
        histroy_condition_headers = {
            'Accept': '*/*',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': self.cookie,
            'Origin': 'https://online.vpbank.com.vn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
            'X-requested-with':'XMLHttpRequest'
        }
        self.retry_transactions += 1
        histroy_condition_response = self.curlPost(self.url["setHistoriesConditions"], data=payload, headers=histroy_condition_headers)

        # session time out 或查询中错误
        error_messages = [
            'Your login session invalid or you have been signed out because you signed in on a different computer or device',
            'Invalid Request',
            "Fatal Error: Object reference not set to an instance of an object.",
            'Lỗi: Phiên đăng nhập không hợp lệ. Quý khách vui lòng thực hiện đăng nhập lại',
            'Lỗi: Yêu cầu không hợp lệ'
        ]
        print('histories condition response: ' + histroy_condition_response)
        # 使用 | 分隔字符串
        response_data = histroy_condition_response.split('|')
        if '00' == response_data[0]:
            account = response_data[1]
            f_date = response_data[2]
            t_date = response_data[3]
            
            # 抓交易记录
            histroy_headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Cookie': self.cookie,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
                
            }
            histroy_url = self.url["getHistories"] + "-" + account + "-" + f_date + "-" + t_date + "--"
            histroy_response = self.curlGet(histroy_url, headers=histroy_headers)
            html_content = histroy_response

            soup = BeautifulSoup(html_content, 'html.parser')
            # 找到指定的 <table>
            table = soup.find('table', {'id': 'acStmtList'})
            # 遍历表格中的所有行
            rows = table.find_all('tr')
            # 提取表头
            header = [th.get_text().replace(" ", "_") for th in rows[0].find_all('th')]
            # 提取每一行的數據
            data = []
            for row in rows[1:]:
                cols = row.find_all('td')
                row_data = [col.get_text().replace("\xa0", " ") for col in cols]
                # header ['Index_#', 'Accounting_Entry', 'Value_date', 'Credit', 'Debit', 'Narrative', 'Running_balance', 'Transaction_time', '#']
                # 将表头与行数据配对，生成字典，并移除Index #, #两个栏位
                row_dict = {key: value for key, value in zip(header, row_data) if key not in ['Index_#', '#']}
                data.append(row_dict)

            # 輸出結果
            # 遍歷資料，過濾出 'Credit' 不為空的行
            credit_data = [row for row in data if row['Credit'].strip() != '']
            for item in credit_data:
                item["Credit"] = item["Credit"].replace(",", "")  # 删除逗号
            
            self.retry_transactions = 0
            return {
                'code':200,
                'success': True, 
                'message': 'Thành công',
                'data':{
                    'transactions':credit_data
                }
            }
        elif '01' == response_data[0] and 'No transaction found within the specified date range. Please try again with a wider date range.' in response_data[1]:
            self.retry_transactions = 0
            return {
                'code':200,
                'success': True, 
                'message': 'Thành công',
                'data':{
                    'transactions':[]
                }
            }
        elif '01' == response_data[0] and response_data[1] in error_messages:
            if self.retry_transactions < 3:
                # session time out 或查询中错误 重新登入
                print('getHistories 重新登入')
                self.is_login = False
                return self. getHistories(self.account_number, 100, from_date, to_date, True)
            else:
                print('histories 查询失败次数过多(retry_transactions: ' + self.retry_transactions + ') return Unknown Error')
                return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        elif 'The requested URL was rejected.' in response_data[0]:
            if self.retry_transactions < 3:
                # session time out 或查询中错误 重新登入
                print('getHistories 重新登入 [Request Rejected]')
                self.is_login = False
                return self. getHistories(self.account_number, 100, from_date, to_date, True)
            else:
                print('histories 查询失败次数过多(retry_transactions: ' + self.retry_transactions + ') return Unknown Error')
                return {'code':520 ,'success': False, 'message': 'Unknown Error!'} 
        else:
            return  {
                "success": False,
                "code": 503,
                "message": "Service Unavailable!"
            }
        
