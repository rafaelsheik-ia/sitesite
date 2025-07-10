import requests
import json
from urllib.parse import urlencode

class BaratoSocialAPI:
    def __init__(self, api_key):
        self.api_url = 'https://baratosociais.com/api/v2'
        self.api_key = api_key

    def order(self, data):
        """Adicionar pedido"""
        post_data = {'key': self.api_key, 'action': 'add', **data}
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def status(self, order_id):
        """Obter status do pedido"""
        post_data = {
            'key': self.api_key,
            'action': 'status',
            'order': order_id
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def multi_status(self, order_ids):
        """Obter status de múltiplos pedidos"""
        post_data = {
            'key': self.api_key,
            'action': 'status',
            'orders': ','.join(map(str, order_ids))
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def services(self):
        """Obter lista de serviços"""
        post_data = {
            'key': self.api_key,
            'action': 'services'
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def refill(self, order_id):
        """Refill de pedido"""
        post_data = {
            'key': self.api_key,
            'action': 'refill',
            'order': order_id
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def multi_refill(self, order_ids):
        """Refill de múltiplos pedidos"""
        post_data = {
            'key': self.api_key,
            'action': 'refill',
            'orders': ','.join(map(str, order_ids))
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def refill_status(self, refill_id):
        """Status do refill"""
        post_data = {
            'key': self.api_key,
            'action': 'refill_status',
            'refill': refill_id
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def multi_refill_status(self, refill_ids):
        """Status de múltiplos refills"""
        post_data = {
            'key': self.api_key,
            'action': 'refill_status',
            'refills': ','.join(map(str, refill_ids))
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def cancel(self, order_ids):
        """Cancelar pedidos"""
        post_data = {
            'key': self.api_key,
            'action': 'cancel',
            'orders': ','.join(map(str, order_ids))
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def balance(self):
        """Obter saldo"""
        post_data = {
            'key': self.api_key,
            'action': 'balance'
        }
        response = self._connect(post_data)
        return json.loads(response) if response else None

    def _connect(self, post_data):
        """Conectar à API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.01; Windows NT 5.0)',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                self.api_url,
                data=urlencode(post_data),
                headers=headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
            else:
                return None
                
        except Exception as e:
            print(f"Erro na conexão com BaratoSocial: {e}")
            return None

