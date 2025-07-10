from flask import Blueprint, jsonify, request, session
from src.models.user import AdminConfig, User, Payment, db
from src.services.mercado_pago import MercadoPagoAPI
from src.routes.user import admin_required
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/config', methods=['GET'])
@admin_required
def get_config():
    """Obter todas as configurações"""
    configs = AdminConfig.query.all()
    config_dict = {config.key: config.value for config in configs}
    
    # Retornar valores completos para o admin poder editar
    # Apenas mascarar na exibição se necessário
    return jsonify(config_dict)

@admin_bp.route('/config', methods=['POST'])
@admin_required
def update_config():
    """Atualizar configurações"""
    data = request.json
    
    for key, value in data.items():
        config = AdminConfig.query.filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = AdminConfig(key=key, value=value)
            db.session.add(config)
    
    db.session.commit()
    
    return jsonify({'message': 'Configurações atualizadas com sucesso'})

@admin_bp.route('/config/<key>', methods=['PUT'])
@admin_required
def update_single_config(key):
    """Atualizar uma configuração específica"""
    data = request.json
    value = data.get('value')
    
    config = AdminConfig.query.filter_by(key=key).first()
    if config:
        config.value = value
    else:
        config = AdminConfig(key=key, value=value)
        db.session.add(config)
    
    db.session.commit()
    
    return jsonify({'message': f'Configuração {key} atualizada com sucesso'})

@admin_bp.route('/test-barato-api', methods=['POST'])
@admin_required
def test_barato_api():
    """Testar conexão com API BaratoSocial"""
    from src.services.barato_social import BaratoSocialAPI
    
    config = AdminConfig.query.filter_by(key='barato_api_key').first()
    if not config or not config.value:
        return jsonify({'success': False, 'message': 'Chave API não configurada'}), 400
    
    try:
        api = BaratoSocialAPI(config.value)
        balance = api.balance()
        
        if balance:
            if isinstance(balance, dict) and 'balance' in balance:
                return jsonify({
                    'success': True,
                    'message': 'Conexão com BaratoSocial estabelecida',
                    'balance': balance['balance']
                })
            elif isinstance(balance, dict) and 'error' in balance:
                return jsonify({
                    'success': False,
                    'message': f'Erro da API: {balance["error"]}'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Resposta inesperada da API',
                    'response': str(balance)
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhuma resposta da API BaratoSocial'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao conectar: {str(e)}'
        }), 500

@admin_bp.route('/test-mercado-pago', methods=['POST'])
@admin_required
def test_mercado_pago():
    """Testar conexão com Mercado Pago"""
    access_token_config = AdminConfig.query.filter_by(key='mp_access_token').first()
    
    if not access_token_config or not access_token_config.value:
        return jsonify({'success': False, 'message': 'Access Token do Mercado Pago não configurado'}), 400
    
    try:
        mp_api = MercadoPagoAPI(access_token_config.value)
        payment_methods = mp_api.get_payment_methods()
        
        if payment_methods:
            return jsonify({
                'success': True,
                'message': 'Conexão com Mercado Pago estabelecida',
                'payment_methods_count': len(payment_methods)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro ao obter métodos de pagamento'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao conectar: {str(e)}'
        }), 500

@admin_bp.route('/dashboard-stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Obter estatísticas para dashboard"""
    from sqlalchemy import func
    from src.models.user import Order
    
    # Usuários totais
    total_users = User.query.count()
    
    # Usuários ativos (com pedidos nos últimos 30 dias)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_users = db.session.query(func.count(func.distinct(Order.user_id))).filter(
        Order.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Pedidos totais
    total_orders = Order.query.count()
    
    # Receita total
    total_revenue = db.session.query(func.sum(Order.charge)).scalar() or 0
    
    # Receita do mês atual
    current_month = datetime.now().replace(day=1)
    monthly_revenue = db.session.query(func.sum(Order.charge)).filter(
        Order.created_at >= current_month
    ).scalar() or 0
    
    # Pedidos pendentes
    pending_orders = Order.query.filter(
        Order.status.in_(['Pending', 'In progress', 'Processing'])
    ).count()
    
    # Saldo total dos usuários
    total_user_balance = db.session.query(func.sum(User.balance)).scalar() or 0
    
    # Pagamentos pendentes
    pending_payments = Payment.query.filter_by(status='pending').count()
    
    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': float(total_revenue),
        'monthly_revenue': float(monthly_revenue),
        'total_user_balance': float(total_user_balance),
        'pending_payments': pending_payments
    })

@admin_bp.route('/recent-activity', methods=['GET'])
@admin_required
def get_recent_activity():
    """Obter atividade recente"""
    from src.models.user import Order
    
    # Pedidos recentes
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Usuários recentes
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Pagamentos recentes
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return jsonify({
        'recent_orders': [order.to_dict() for order in recent_orders],
        'recent_users': [user.to_dict() for user in recent_users],
        'recent_payments': [payment.to_dict() for payment in recent_payments]
    })

@admin_bp.route('/payments', methods=['GET'])
@admin_required
def get_all_payments():
    """Listar todos os pagamentos"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    
    query = Payment.query
    
    if status:
        query = query.filter_by(status=status)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payments': [payment.to_dict() for payment in payments.items],
        'total': payments.total,
        'pages': payments.pages,
        'current_page': page
    })

@admin_bp.route('/payments/<int:payment_id>/approve', methods=['POST'])
@admin_required
def approve_payment(payment_id):
    """Aprovar pagamento manualmente"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != 'pending':
        return jsonify({'error': 'Pagamento não está pendente'}), 400
    
    # Adicionar saldo ao usuário
    user = User.query.get(payment.user_id)
    user.balance += payment.amount
    
    # Atualizar status do pagamento
    payment.status = 'approved'
    
    db.session.commit()
    
    return jsonify({
        'message': 'Pagamento aprovado com sucesso',
        'payment': payment.to_dict(),
        'user_new_balance': user.balance
    })

@admin_bp.route('/payments/<int:payment_id>/reject', methods=['POST'])
@admin_required
def reject_payment(payment_id):
    """Rejeitar pagamento"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != 'pending':
        return jsonify({'error': 'Pagamento não está pendente'}), 400
    
    payment.status = 'rejected'
    db.session.commit()
    
    return jsonify({
        'message': 'Pagamento rejeitado',
        'payment': payment.to_dict()
    })

@admin_bp.route('/sync-services', methods=['POST'])
@admin_required
def sync_services():
    """Sincronizar serviços com BaratoSocial"""
    from src.services.barato_social import BaratoSocialAPI
    from src.models.user import Service
    
    config = AdminConfig.query.filter_by(key='barato_api_key').first()
    if not config or not config.value:
        return jsonify({'error': 'Chave API do BaratoSocial não configurada'}), 400
    
    try:
        api = BaratoSocialAPI(config.value)
        services_data = api.services()
        
        if not services_data:
            return jsonify({'error': 'Erro ao obter serviços da API'}), 500
        
        updated_count = 0
        new_count = 0
        
        for service_data in services_data:
            existing_service = Service.query.filter_by(service_id=service_data['service']).first()
            
            if existing_service:
                existing_service.name = service_data['name']
                existing_service.type = service_data['type']
                existing_service.rate = float(service_data['rate'])
                existing_service.min = int(service_data['min'])
                existing_service.max = int(service_data['max'])
                existing_service.category = service_data.get('category', '')
                updated_count += 1
            else:
                new_service = Service(
                    service_id=service_data['service'],
                    name=service_data['name'],
                    type=service_data['type'],
                    rate=float(service_data['rate']),
                    min=int(service_data['min']),
                    max=int(service_data['max']),
                    category=service_data.get('category', '')
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

