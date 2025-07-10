import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.services import services_bp
from src.routes.orders import orders_bp
from src.routes.admin import admin_bp
from src.routes.payments import payments_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Habilitar CORS
CORS(app, supports_credentials=True)

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(services_bp, url_prefix='/api')
app.register_blueprint(orders_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(payments_bp, url_prefix='/api/payments')

# ====================================================================
# ROTA DE HEALTH CHECK ADICIONADA PARA O RENDER.COM
# ====================================================================
@app.route('/api/health')
def health_check():
    # Esta rota simples retorna um status "ok" para que o Render
    # saiba que a aplicação está funcionando corretamente.
    return {"status": "ok"}, 200
# ====================================================================

# Configuração do banco de dados
# O caminho do banco de dados será ajustado para funcionar com o disco do Render
database_dir = os.path.join(os.path.dirname(__file__), 'database')
os.makedirs(database_dir, exist_ok=True) # Garante que o diretório exista
database_path = os.path.join(database_dir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()
    
    # Criar configurações padrão se não existirem
    from src.models.user import AdminConfig
    
    default_configs = {
        'profit_margin': '20',  # 20% de margem de lucro padrão
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

# As rotas abaixo servem para o frontend, mas como o frontend está no Netlify,
# elas não serão muito usadas. Mantemos por segurança.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# O bloco if __name__ == '__main__': foi removido pois o Gunicorn (servidor de produção)
# irá importar e rodar a variável 'app' diretamente.
