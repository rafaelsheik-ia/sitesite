#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.models.user import db, AdminConfig

def init_default_config():
    """Inicializar configurações padrão"""
    with app.app_context():
        # Configurações padrão com as credenciais fornecidas
        default_configs = {
            'barato_api_key': '9e0da2b1a6087d34075c123940e7fab5',
            'profit_margin': '20',
            'mp_access_token': 'APP_USR-4278668979689090-070320-0c429f571f0cc84734fbf354e55a26fe-1766003359',
            'mp_public_key': 'APP_USR-25688d4e-0983-41b0-b4e8-bb5c5c13737d',
            'mp_client_id': '4278668979689090',
            'mp_client_secret': 'ZjgOAqTY8QUXT4pOpa8erXTOnv2Qc6SO'
        }
        
        for key, value in default_configs.items():
            # Verificar se configuração já existe
            config = AdminConfig.query.filter_by(key=key).first()
            if not config:
                config = AdminConfig(key=key, value=value)
                db.session.add(config)
                print(f"Configuração {key} criada")
            else:
                # Atualizar se valor estiver vazio
                if not config.value:
                    config.value = value
                    print(f"Configuração {key} atualizada")
                else:
                    print(f"Configuração {key} já existe")
        
        db.session.commit()
        print("Configurações inicializadas com sucesso!")

if __name__ == '__main__':
    init_default_config()

