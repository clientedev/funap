
import requests
import sys

BASE_URL = "https://funap-production.up.railway.app"

def test_flow():
    session = requests.Session()
    
    print("Testing Login...")
    login_data = {"username": "gabriel@funap.com.br", "password": "123"}
    # Use 123456 as seen in previous turns
    r = session.post(f"{BASE_URL}/login", data={"username": "gabriel@funap.com.br", "password": "123"}, allow_redirects=True)
    if "Dashboard" not in r.text:
       print("Login with '123' failed, trying '123456'...")
       r = session.post(f"{BASE_URL}/login", data={"username": "gabriel@funap.com.br", "password": "123456"}, allow_redirects=True)
    
    if "Dashboard" in r.text:
        print("✅ Login Successful")
    else:
        print("❌ Login Failed")
        print("Response Snippet:", r.text[:1000])
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
        "objeto": "TESTE FINAL RESTAURAÇÃO V23",
        "modalidade": "VENDA",
        "processo_sei": "123/2026",
        "numero": f"TESTE-{sys.version[:3]}"
    }
    r = session.post(f"{BASE_URL}/vendas/nova", data=venda_data, allow_redirects=True)
    
    if r.status_code == 200 and "Venda #" in r.text:
        print("✅ VENDA CREATED SUCCESSFULLY! OID Ghost 21978 has been EXORCISED.")
    elif "cache lookup failed for type" in r.text or "21978" in r.text:
        print("❌ THE GHOST PERSISTS. OID 21978 detected.")
        print(r.text[:500])
    else:
        print(f"❓ Unexpected result: {r.status_code}")
        print(r.text[:500])

if __name__ == "__main__":
    test_flow()
