from flask import Blueprint, jsonify, request, session
from src.models.user import Service, AdminConfig, db
from src.services.barato_social import BaratoSocialAPI
from src.routes.user import login_required, admin_required

services_bp = Blueprint('services', __name__)

def get_barato_api():
    """Obter instância da API BaratoSocial"""
    config = AdminConfig.query.filter_by(key='barato_api_key').first()
    if not config or not config.value:
        return None
    return BaratoSocialAPI(config.value)

@services_bp.route('/services', methods=['GET'])
@login_required
def get_services():
    """Listar serviços disponíveis"""
    # Obter margem de lucro
    profit_config = AdminConfig.query.filter_by(key='profit_margin').first()
    profit_margin = float(profit_config.value) if profit_config and profit_config.value else 0
    
    # Verificar se há serviços na base de dados
    services = Service.query.filter_by(is_active=True).all()
    
    # Se não há serviços, tentar sincronizar automaticamente
    if not services:
        api = get_barato_api()
        if api:
            try:
                services_data = api.services()
                if services_data:
                    # Sincronizar serviços
                    for service_data in services_data:
                        new_service = Service(
                            service_id=service_data['service'],
                            name=service_data['name'],
                            type=service_data['type'],
                            rate=float(service_data['rate']),
                            min=int(service_data['min']),
                            max=int(service_data['max']),
                            category=service_data.get('category', ''),
                            description=service_data.get('description', '')
                        )
                        db.session.add(new_service)
                    
                    db.session.commit()
                    services = Service.query.filter_by(is_active=True).all()
            except Exception as e:
                print(f"Erro ao sincronizar serviços automaticamente: {e}")
    
    return jsonify([service.to_dict(profit_margin) for service in services])

@services_bp.route('/services/categories', methods=['GET'])
@login_required
def get_categories():
    """Listar categorias de serviços"""
    categories = db.session.query(Service.category).filter(
        Service.is_active == True,
        Service.category.isnot(None)
    ).distinct().all()
    
    return jsonify([cat[0] for cat in categories if cat[0]])

@services_bp.route('/services/sync', methods=['POST'])
@admin_required
def sync_services():
    """Sincronizar serviços com BaratoSocial"""
    api = get_barato_api()
    if not api:
        return jsonify({'error': 'Chave API do BaratoSocial não configurada'}), 400
    
    try:
        # Obter serviços da API
        services_data = api.services()
        
        if not services_data:
            return jsonify({'error': 'Erro ao obter serviços da API'}), 500
        
        updated_count = 0
        new_count = 0
        
        for service_data in services_data:
            # Verificar se serviço já existe
            existing_service = Service.query.filter_by(service_id=service_data['service']).first()
            
            if existing_service:
                # Atualizar serviço existente
                existing_service.name = service_data['name']
                existing_service.type = service_data['type']
                existing_service.rate = float(service_data['rate'])
                existing_service.min = int(service_data['min'])
                existing_service.max = int(service_data['max'])
                existing_service.category = service_data.get('category', '')
                existing_service.description = service_data.get('description', '')
                updated_count += 1
            else:
                # Criar novo serviço
                new_service = Service(
                    service_id=service_data['service'],
                    name=service_data['name'],
                    type=service_data['type'],
                    rate=float(service_data['rate']),
                    min=int(service_data['min']),
                    max=int(service_data['max']),
                    category=service_data.get('category', ''),
                    description=service_data.get('description', '')
                )
                db.session.add(new_service)
                new_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Serviços sincronizados com sucesso',
            'new_services': new_count,
            'updated_services': updated_count
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao sincronizar serviços: {str(e)}'}), 500

@services_bp.route('/services/<int:service_id>', methods=['GET'])
@login_required
def get_service(service_id):
    """Obter detalhes de um serviço"""
    service = Service.query.get_or_404(service_id)
    
    # Obter margem de lucro
    profit_config = AdminConfig.query.filter_by(key='profit_margin').first()
    profit_margin = float(profit_config.value) if profit_config and profit_config.value else 0
    
    return jsonify(service.to_dict(profit_margin))

@services_bp.route('/services/<int:service_id>/toggle', methods=['POST'])
@admin_required
def toggle_service(service_id):
    """Ativar/desativar serviço"""
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    
    return jsonify({
        'message': f'Serviço {"ativado" if service.is_active else "desativado"} com sucesso',
        'service': service.to_dict()
    })

@services_bp.route('/services/search', methods=['GET'])
@login_required
def search_services():
    """Buscar serviços"""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Obter margem de lucro
    profit_config = AdminConfig.query.filter_by(key='profit_margin').first()
    profit_margin = float(profit_config.value) if profit_config and profit_config.value else 0
    
    # Construir query
    services_query = Service.query.filter_by(is_active=True)
    
    if query:
        services_query = services_query.filter(
            Service.name.contains(query) | 
            Service.description.contains(query)
        )
    
    if category:
        services_query = services_query.filter_by(category=category)
    
    services = services_query.all()
    
    return jsonify([service.to_dict(profit_margin) for service in services])

