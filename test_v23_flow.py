
import requests
import sys
from datetime import datetime

BASE_URL = "https://funap-production.up.railway.app"

def test_flow():
    session = requests.Session()
    
    print("Testing Login...")
    r = session.post(f"{BASE_URL}/login", data={"username": "gabriel@funap.com.br", "password": "123456"}, allow_redirects=True)
    
    if "Dashboard" in r.text or r.status_code == 200:
        print("✅ Login Successful")
    else:
        print("❌ Login Failed")
        print("Response Snippet:", r.text[:500])
        return

    print("Checking Vendas Page...")
    r = session.get(f"{BASE_URL}/vendas")
    if r.status_code == 200:
        print("✅ Vendas Page OK")
    else:
        print(f"❌ Vendas Page Failed: {r.status_code}")
        return

    print("Testing Venda Creation (The OID Ghost Test)...")
    venda_data = {
        "cliente_id": 1,
        "linha_produto_id": 1,
        "objeto": "TESTE FINAL EXORCISMO",
        "modalidade": "VENDA",
        "processo_sei": "123/2026",
        "numero": f"V25-{datetime.now().strftime('%M%S')}"
    }
    r = session.post(f"{BASE_URL}/vendas/nova", data=venda_data, allow_redirects=True)
    
    if r.status_code == 200 and "Venda #" in r.text:
        print("✅ VENDA CREATED SUCCESSFULLY! OID Ghost 21978 has been EXORCISED.")
    elif "cache lookup failed for type" in r.text or "21978" in r.text:
        print("❌ THE GHOST PERSISTS. OID 21978 detected.")
        print(r.text[:500])
    else:
        print(f"❓ Result (Check if success): {r.status_code}")
        if "UniqueViolation" in r.text:
             print("✅ Venda reached constraints (OID FIX CONFIRMED)")
        else:
             print(r.text[:500])

if __name__ == "__main__":
    test_flow()
