
import requests
from datetime import datetime

BASE_URL = "https://funap-production.up.railway.app"

def test_login():
    session = requests.Session()
    print(f"Testing Login at {datetime.now()}...")
    try:
        r = session.post(f"{BASE_URL}/login", data={"username": "gabriel@funap.com.br", "password": "123456"}, allow_redirects=True, timeout=10)
        if "Dashboard" in r.text or r.status_code == 200:
            if "detail" in r.text and "Erro interno" in r.text:
                print("❌ Login Failed with Server Error:")
                print(r.text[:500])
            else:
                print("✅ Login Successful")
        else:
            print(f"❌ Login Failed: {r.status_code}")
            print(r.text[:500])
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_login()
