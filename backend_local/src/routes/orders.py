from flask import Blueprint, jsonify, request, session
from src.models.user import User, Order, Service, AdminConfig, db
from src.services.barato_social import BaratoSocialAPI
from src.routes.user import login_required, admin_required

orders_bp = Blueprint('orders', __name__)

def get_barato_api():
    """Obter instância da API BaratoSocial"""
    config = AdminConfig.query.filter_by(key='barato_api_key').first()
    if not config or not config.value:
        return None
    return BaratoSocialAPI(config.value)

@orders_bp.route('/orders', methods=['POST'])
@login_required
def create_order():
    """Criar novo pedido"""
    data = request.json
    user = User.query.get(session['user_id'])
    
    # Validações
    required_fields = ['service_id', 'link', 'quantity']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    # Obter serviço
    service = Service.query.filter_by(service_id=data['service_id'], is_active=True).first()
    if not service:
        return jsonify({'error': 'Serviço não encontrado ou inativo'}), 404
    
    # Validar quantidade
    quantity = int(data['quantity'])
    if quantity < service.min or quantity > service.max:
        return jsonify({'error': f'Quantidade deve estar entre {service.min} e {service.max}'}), 400
    
    # Calcular preço
    profit_config = AdminConfig.query.filter_by(key='profit_margin').first()
    profit_margin = float(profit_config.value) if profit_config and profit_config.value else 0
    
    final_rate = service.get_final_price(profit_margin)
    total_charge = (final_rate * quantity) / 1000  # Preço por 1000
    
    # Verificar saldo
    if user.balance < total_charge:
        return jsonify({'error': 'Saldo insuficiente'}), 400
    
    # Obter API
    api = get_barato_api()
    if not api:
        return jsonify({'error': 'API BaratoSocial não configurada'}), 500
    
    try:
        # Preparar dados para API
        order_data = {
            'service': service.service_id,
            'link': data['link'],
            'quantity': quantity
        }
        
        # Adicionar campos opcionais
        if data.get('comments'):
            order_data['comments'] = data['comments']
        if data.get('runs'):
            order_data['runs'] = data['runs']
        if data.get('interval'):
            order_data['interval'] = data['interval']
        
        # Criar pedido na API
        api_response = api.order(order_data)
        
        if not api_response or 'error' in api_response:
            error_msg = api_response.get('error', 'Erro desconhecido na API') if api_response else 'Erro na comunicação com API'
            return jsonify({'error': error_msg}), 500
        
        # Debitar saldo do usuário
        user.balance -= total_charge
        
        # Criar pedido no banco
        order = Order(
            user_id=user.id,
            service_id=service.service_id,
            service_name=service.name,
            link=data['link'],
            quantity=quantity,
            charge=total_charge,
            barato_order_id=api_response.get('order'),
            status='Pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify({
            'message': 'Pedido criado com sucesso',
            'order': order.to_dict(),
            'remaining_balance': user.balance
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Erro ao criar pedido: {str(e)}'}), 500

@orders_bp.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Listar pedidos do usuário"""
    user = User.query.get(session['user_id'])
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'orders': [order.to_dict() for order in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page
    })

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Obter detalhes de um pedido"""
    user = User.query.get(session['user_id'])
    order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
    
    return jsonify(order.to_dict())

@orders_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    """Atualizar status do pedido"""
    user = User.query.get(session['user_id'])
    order = Order.query.filter_by(id=order_id, user_id=user.id).first_or_404()
    
    if not order.barato_order_id:
        return jsonify({'error': 'Pedido não possui ID da API'}), 400
    
    api = get_barato_api()
    if not api:
        return jsonify({'error': 'API BaratoSocial não configurada'}), 500
    
    try:
        # Obter status da API
        status_response = api.status(order.barato_order_id)
        
        if status_response and 'status' in status_response:
            order.status = status_response['status']
            if 'start_count' in status_response:
                order.start_count = status_response['start_count']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Status atualizado',
                'order': order.to_dict()
            })
        else:
            return jsonify({'error': 'Erro ao obter status da API'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao atualizar status: {str(e)}'}), 500

@orders_bp.route('/orders/sync-status', methods=['POST'])
@login_required
def sync_all_orders_status():
    """Sincronizar status de todos os pedidos pendentes"""
    user = User.query.get(session['user_id'])
    
    # Obter pedidos pendentes
    pending_orders = Order.query.filter_by(
        user_id=user.id
    ).filter(
        Order.status.in_(['Pending', 'In progress', 'Processing'])
    ).filter(
        Order.barato_order_id.isnot(None)
    ).all()
    
    if not pending_orders:
        return jsonify({'message': 'Nenhum pedido pendente encontrado'})
    
    api = get_barato_api()
    if not api:
        return jsonify({'error': 'API BaratoSocial não configurada'}), 500
    
    try:
        # Obter IDs dos pedidos
        order_ids = [order.barato_order_id for order in pending_orders]
        
        # Obter status em lote
        status_response = api.multi_status(order_ids)
        
        if status_response:
            updated_count = 0
            
            for order in pending_orders:
                # Encontrar status correspondente
                order_status = next(
                    (item for item in status_response if str(item.get('order')) == str(order.barato_order_id)),
                    None
                )
                
                if order_status and 'status' in order_status:
                    order.status = order_status['status']
                    if 'start_count' in order_status:
                        order.start_count = order_status['start_count']
                    updated_count += 1
            
            db.session.commit()
            
            return jsonify({
                'message': f'{updated_count} pedidos atualizados',
                'updated_count': updated_count
            })
        else:
            return jsonify({'error': 'Erro ao obter status da API'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao sincronizar status: {str(e)}'}), 500

# Rotas administrativas
@orders_bp.route('/admin/orders', methods=['GET'])
@admin_required
def get_all_orders():
    """Listar todos os pedidos (admin)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    orders = Order.query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'orders': [order.to_dict() for order in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page
    })

@orders_bp.route('/admin/orders/stats', methods=['GET'])
@admin_required
def get_orders_stats():
    """Estatísticas de pedidos (admin)"""
    from sqlalchemy import func
    
    # Total de pedidos
    total_orders = Order.query.count()
    
    # Pedidos por status
    status_stats = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()
    
    # Receita total
    total_revenue = db.session.query(func.sum(Order.charge)).scalar() or 0
    
    # Pedidos hoje
    from datetime import datetime, timedelta
    today = datetime.now().date()
    orders_today = Order.query.filter(
        func.date(Order.created_at) == today
    ).count()
    
    return jsonify({
        'total_orders': total_orders,
        'orders_today': orders_today,
        'total_revenue': float(total_revenue),
        'status_distribution': [{'status': stat[0], 'count': stat[1]} for stat in status_stats]
    })

