import requests
import json
from datetime import datetime, timedelta

class MercadoPagoAPI:
    def __init__(self, access_token, public_key=None):
        self.access_token = access_token
        self.public_key = public_key
        self.base_url = 'https://api.mercadopago.com'

    def create_payment(self, amount, description, payer_email, external_reference=None):
        """Criar pagamento via PIX"""
        url = f"{self.base_url}/v1/payments"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Data de expiração (30 minutos)
        expiration_date = datetime.now() + timedelta(minutes=30)
        
        payment_data = {
            "transaction_amount": float(amount),
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": payer_email
            },
            "date_of_expiration": expiration_date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        }
        
        if external_reference:
            payment_data["external_reference"] = str(external_reference)
        
        try:
            response = requests.post(url, headers=headers, json=payment_data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Erro ao criar pagamento: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def get_payment(self, payment_id):
        """Obter informações do pagamento"""
        url = f"{self.base_url}/v1/payments/{payment_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao obter pagamento: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def create_preference(self, items, back_urls=None, external_reference=None):
        """Criar preferência de pagamento (para checkout)"""
        url = f"{self.base_url}/checkout/preferences"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        preference_data = {
            "items": items,
            "payment_methods": {
                "excluded_payment_types": [],
                "installments": 1
            },
            "auto_return": "approved"
        }
        
        if back_urls:
            preference_data["back_urls"] = back_urls
            
        if external_reference:
            preference_data["external_reference"] = str(external_reference)
        
        try:
            response = requests.post(url, headers=headers, json=preference_data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Erro ao criar preferência: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def get_payment_methods(self):
        """Obter métodos de pagamento disponíveis"""
        url = f"{self.base_url}/v1/payment_methods"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro ao obter métodos de pagamento: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

