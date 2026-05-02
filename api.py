import requests

def truewallet(phone,linkgift):
    resp = requests.post(f"https://gift.truemoney.com/campaign/vouchers/{linkgift}/redeem",json={"mobile": phone,"voucher_hash": linkgift},headers={"Accept": "application/json","User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36","Content-Type": "application/json"})
    if resp.status_code == 200:
        return True, resp.json()
    else:return False, None