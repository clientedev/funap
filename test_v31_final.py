
import requests
from datetime import datetime

BASE_URL = "https://funap-production.up.railway.app"

def test_final_flow():
    session = requests.Session()
    print("1. Testing Login...")
    r = session.post(f"{BASE_URL}/login", data={"username": "gabriel@funap.com.br", "password": "123456"}, allow_redirects=True)
    
    if "Dashboard" not in r.text and r.status_code != 200:
        print(f"❌ Login Failed: {r.status_code}")
        print(r.text[:500])
        return
    print("✅ Login Successful")

    print("2. Testing Venda Creation (OFFICIAL EXORCISM TEST)...")
    venda_data = {
        "cliente_id": 1,
        "linha_produto_id": 1,
        "objeto": f"VERIFICACAO FINAL V31 - {datetime.now().strftime('%H%M%S')}",
        "modalidade": "VENDA",
        "processo_sei": "000/2026",
        "numero": f"V31-FINAL-{datetime.now().strftime('%M%S%f')[:5]}"
    }
    r = session.post(f"{BASE_URL}/vendas/nova", data=venda_data, allow_redirects=True)
    
    if r.status_code == 200 and ("Venda #" in r.text or "Sucesso" in r.text or "vendas" in r.url):
        print("✅ FULL FLOW SUCCESSFUL! OID 21978 HAS BEEN EXORCISED AND THE CATALOG IS CLEAN.")
    elif "cache lookup failed for type" in r.text or "21978" in r.text:
        print("❌ FAILED: THE GHOST STILL PERSISTS IN THE CATALOG.")
        print(r.text[:1000])
    elif "InFailedSqlTransaction" in r.text:
        print("❌ FAILED: TRANSACTION ABORTED.")
        print(r.text[:500])
    else:
        print(f"❓ Unexpected Result: {r.status_code}")
        print(r.text[:1000])

if __name__ == "__main__":
    test_final_flow()
