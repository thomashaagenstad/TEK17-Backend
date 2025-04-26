import requests

url = "http://127.0.0.1:8000/chat"
data = {"question": "Hva er krav til brannmotstand for bærende konstruksjoner i brannklasse 3?"}

response = requests.post(url, json=data)
print("Svar fra backend:", response.json())
