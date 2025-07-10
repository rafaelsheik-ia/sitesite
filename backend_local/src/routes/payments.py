from flask import Blueprint, jsonify, request, session
from src.models.user import User, Payment, AdminConfig, db
from src.services.mercado_pago import MercadoPagoAPI
from src.routes.user import login_required

payments_bp = Blueprint('payments', __name__)

def get_mercado_pago_api():
    """Obter instância da API Mercado Pago"""
    access_token_config = AdminConfig.query.filter_by(key='mp_access_token').first()
    public_key_config = AdminConfig.query.filter_by(key='mp_public_key').first()
    
    if not access_token_config or not access_token_config.value:
        return None
    
    public_key = public_key_config.value if public_key_config else None
    return MercadoPagoAPI(access_token_config.value, public_key)

@payments_bp.route('/create-payment', methods=['POST'])
@login_required
def create_payment():
    """Criar pagamento PIX"""
    data = request.json
    user = User.query.get(session['user_id'])
    
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Valor inválido'}), 400
    
    # Valor mínimo
    if amount < 1:
        return jsonify({'error': 'Valor mínimo é R$ 1,00'}), 400
    
    mp_api = get_mercado_pago_api()
    if not mp_api:
        return jsonify({'error': 'Mercado Pago não configurado'}), 500
    
    try:
        # Criar registro de pagamento local
        payment = Payment(
            user_id=user.id,
            amount=amount,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Criar pagamento no Mercado Pago
        mp_payment = mp_api.create_payment(
            amount=amount,
            description=f'Recarga de saldo - INFLUENCIANDO - ID: {payment.id}',
            payer_email=user.email,
            external_reference=str(payment.id)
        )
        
        if mp_payment and mp_payment.get('id'):
            # Atualizar pagamento com ID do Mercado Pago
            payment.payment_id = str(mp_payment['id'])
            db.session.commit()
            
            # Extrair informações do PIX
            pix_info = {}
            if 'point_of_interaction' in mp_payment:
                transaction_data = mp_payment['point_of_interaction'].get('transaction_data', {})
                pix_info = {
                    'qr_code': transaction_data.get('qr_code', ''),
                    'qr_code_base64': transaction_data.get('qr_code_base64', ''),
                    'ticket_url': transaction_data.get('ticket_url', '')
                }
            
            return jsonify({
                'payment_id': payment.id,
                'mp_payment_id': mp_payment['id'],
                'amount': amount,
                'status': mp_payment.get('status', 'pending'),
                'pix_info': pix_info,
                'expires_at': mp_payment.get('date_of_expiration')
            })
        else:
            # Remover pagamento local se falhou no MP
            db.session.delete(payment)
            db.session.commit()
            return jsonify({'error': 'Erro ao criar pagamento no Mercado Pago'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao criar pagamento: {str(e)}'}), 500

@payments_bp.route('/check-payment/<int:payment_id>', methods=['GET'])
@login_required
def check_payment(payment_id):
    """Verificar status do pagamento"""
    user = User.query.get(session['user_id'])
    payment = Payment.query.filter_by(id=payment_id, user_id=user.id).first_or_404()
    
    if not payment.payment_id:
        return jsonify({'error': 'Pagamento não possui ID do Mercado Pago'}), 400
    
    mp_api = get_mercado_pago_api()
    if not mp_api:
        return jsonify({'error': 'Mercado Pago não configurado'}), 500
    
    try:
        mp_payment = mp_api.get_payment(payment.payment_id)
        
        if mp_payment:
            old_status = payment.status
            new_status = mp_payment.get('status', 'pending')
            
            # Mapear status do MP para nosso sistema
            status_mapping = {
                'approved': 'approved',
                'pending': 'pending',
                'in_process': 'pending',
                'rejected': 'rejected',
                'cancelled': 'cancelled',
                'refunded': 'refunded'
            }
            
            mapped_status = status_mapping.get(new_status, 'pending')
            payment.status = mapped_status
            
            # Se pagamento foi aprovado, adicionar saldo
            if old_status != 'approved' and mapped_status == 'approved':
                user.balance += payment.amount
            
            db.session.commit()
            
            return jsonify({
                'payment_id': payment.id,
                'status': payment.status,
                'mp_status': new_status,
                'amount': payment.amount,
                'user_balance': user.balance
            })
        else:
            return jsonify({'error': 'Erro ao consultar pagamento no Mercado Pago'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao verificar pagamento: {str(e)}'}), 500

@payments_bp.route('/webhook', methods=['POST'])
def mercado_pago_webhook():
    """Webhook do Mercado Pago"""
    try:
        data = request.json
        
        # Verificar se é notificação de pagamento
        if data.get('type') == 'payment':
            payment_id = data.get('data', {}).get('id')
            
            if payment_id:
                # Buscar pagamento local pelo MP ID
                payment = Payment.query.filter_by(payment_id=str(payment_id)).first()
                
                if payment:
                    mp_api = get_mercado_pago_api()
                    if mp_api:
                        mp_payment = mp_api.get_payment(payment_id)
                        
                        if mp_payment:
                            old_status = payment.status
                            new_status = mp_payment.get('status', 'pending')
                            
                            # Mapear status
                            status_mapping = {
                                'approved': 'approved',
                                'pending': 'pending',
                                'in_process': 'pending',
                                'rejected': 'rejected',
                                'cancelled': 'cancelled',
                                'refunded': 'refunded'
                            }
                            
                            mapped_status = status_mapping.get(new_status, 'pending')
                            payment.status = mapped_status
                            
                            # Se pagamento foi aprovado, adicionar saldo
                            if old_status != 'approved' and mapped_status == 'approved':
                                user = User.query.get(payment.user_id)
                                if user:
                                    user.balance += payment.amount
                            
                            db.session.commit()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@payments_bp.route('/payment-methods', methods=['GET'])
@login_required
def get_payment_methods():
    """Obter métodos de pagamento disponíveis"""
    mp_api = get_mercado_pago_api()
    if not mp_api:
        return jsonify({'error': 'Mercado Pago não configurado'}), 500
    
    try:
        methods = mp_api.get_payment_methods()
        
        if methods:
            # Filtrar apenas PIX e cartões
            filtered_methods = [
                method for method in methods 
                if method.get('id') in ['pix', 'credit_card', 'debit_card']
            ]
            return jsonify(filtered_methods)
        else:
            return jsonify({'error': 'Erro ao obter métodos de pagamento'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao obter métodos: {str(e)}'}), 500

@payments_bp.route('/create-preference', methods=['POST'])
@login_required
def create_preference():
    """Criar preferência de pagamento (checkout)"""
    data = request.json
    user = User.query.get(session['user_id'])
    
    amount = data.get('amount')
    if not amount or amount <= 0:
        return jsonify({'error': 'Valor inválido'}), 400
    
    mp_api = get_mercado_pago_api()
    if not mp_api:
        return jsonify({'error': 'Mercado Pago não configurado'}), 500
    
    try:
        # Criar registro de pagamento local
        payment = Payment(
            user_id=user.id,
            amount=amount,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Criar preferência no Mercado Pago
        items = [{
            'title': f'Recarga de saldo - INFLUENCIANDO',
            'quantity': 1,
            'unit_price': float(amount),
            'currency_id': 'BRL'
        }]
        
        back_urls = {
            'success': request.host_url + 'payment-success',
            'failure': request.host_url + 'payment-failure',
            'pending': request.host_url + 'payment-pending'
        }
        
        preference = mp_api.create_preference(
            items=items,
            back_urls=back_urls,
            external_reference=str(payment.id)
        )
        
        if preference and preference.get('id'):
            return jsonify({
                'preference_id': preference['id'],
                'payment_id': payment.id,
                'init_point': preference.get('init_point'),
                'sandbox_init_point': preference.get('sandbox_init_point')
            })
        else:
            db.session.delete(payment)
            db.session.commit()
            return jsonify({'error': 'Erro ao criar preferência de pagamento'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Erro ao criar preferência: {str(e)}'}), 500

