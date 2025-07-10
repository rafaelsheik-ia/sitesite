#!/usr/bin/env python3
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from src.models.user import db, AdminConfig

# Criar app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar banco
db.init_app(app)

with app.app_context():
    # Deletar todas as tabelas
    db.drop_all()
    
    # Criar todas as tabelas
    db.create_all()
    
    # Criar configurações padrão
    default_configs = {
        'profit_margin': '20',
        'barato_api_key': '',
        'mp_access_token': '',
        'mp_public_key': '',
        'mp_client_id': '',
        'mp_client_secret': ''
    }
    
    for key, default_value in default_configs.items():
        existing_config = AdminConfig.query.filter_by(key=key).first()
        if not existing_config:
            config = AdminConfig(key=key, value=default_value)
            db.session.add(config)
    
    db.session.commit()
    print("Banco de dados inicializado com sucesso!")

