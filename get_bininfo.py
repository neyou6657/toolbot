from curl_cffi import requests
from bs4 import BeautifulSoup
import re


class BinInfoFetcher:
    """BIN信息获取器 - 根据BIN获取卡信息和对应国家的账单地址"""
    
    def __init__(self):
        self.session = requests.Session(impersonate="Chrome124")
        self.session2 = requests.Session(impersonate="Chrome124")
        # 初始化bincheck.io的session
        self.session.get("https://bincheck.io/zh")
    
    def get_bin_info(self, bin_number: str) -> dict:
        """
        获取BIN信息
        :param bin_number: BIN号（前6位）
        :return: 包含卡信息的字典
        """
        url = f"https://bincheck.io/zh/details/{bin_number}"
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        container = soup.find('div', class_='overflow-x-auto')
        if not container:
            return None
        
        tables = container.find_all('table')
        info = {}
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    link = cells[1].find('a')
                    value = link.get_text(strip=True) if link else cells[1].get_text(strip=True)
                    info[label] = value
        
        return {
            'country': info.get('ISO 国家名称'),
            'country_code': info.get('ISO 国家代码 A2', '').upper(),
            'card_brand': info.get('卡牌'),
            'card_type': info.get('卡的种类'),
            'bank': info.get('发行人名称/银行')
        }
    
    def get_fake_address(self, country_code: str) -> dict:
        """
        获取指定国家的假地址
        :param country_code: 国家代码 (如 US, IN, JP)
        :return: 包含地址信息的字典
        """
        url = f"https://fakeit.receivefreesms.co.uk/c/{country_code.lower()}/"
        resp = self.session2.get(url)
        text = resp.text
        
        def extract_value(field_id):
            pattern = rf"getElementById\('{field_id}'\)\.textContent=\"([^\"]*)\""
            match = re.search(pattern, text)
            return match.group(1) if match else None
        
        return {
            'name': extract_value('nameLoading'),
            'address': extract_value('addressLoading'),
            'city': extract_value('cityLoading'),
            'postcode': extract_value('postcodeLoading'),
            'phone': extract_value('phoneLoading'),
            'email': extract_value('cemailLoading'),  # 公司邮箱
        }
    
    def get_billing_info(self, bin_number: str) -> dict:
        """
        一站式获取卡信息和账单地址
        :param bin_number: BIN号（前6位）
        :return: 包含完整账单信息的字典
        """
        # 获取BIN信息
        bin_info = self.get_bin_info(bin_number)
        if not bin_info or not bin_info.get('country_code'):
            return None
        
        # 获取对应国家的假地址
        fake_addr = self.get_fake_address(bin_info['country_code'])
        
        return {
            'bin_info': bin_info,
            'billing': {
                'name': fake_addr.get('name'),
                'address_line1': fake_addr.get('address'),
                'city': fake_addr.get('city'),
                'postal_code': fake_addr.get('postcode'),
                'country': bin_info.get('country'),
                'country_code': bin_info.get('country_code'),
                'phone': fake_addr.get('phone'),
                'email': fake_addr.get('email'),
            }
        }


if __name__ == '__main__':
    # 测试
    fetcher = BinInfoFetcher()
    
    # 测试BIN: 551827 (美国)
    result = fetcher.get_billing_info('548108')
    if result:
        print("=== BIN信息 ===")
        for k, v in result['bin_info'].items():
            print(f"  {k}: {v}")
        
        print("\n=== 账单地址 ===")
        for k, v in result['billing'].items():
            print(f"  {k}: {v}")