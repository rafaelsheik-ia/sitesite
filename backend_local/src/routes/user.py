from flask import Blueprint, jsonify, request, session
from src.models.user import User, Payment, db
from functools import wraps

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # Validações
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    # Verificar se usuário já existe
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Nome de usuário já existe'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
    
    # Criar usuário
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    
    # Primeiro usuário é admin
    if User.query.count() == 0:
        user.is_admin = True
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Usuário criado com sucesso', 'user': user.to_dict()}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username e senha são obrigatórios'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        return jsonify({'message': 'Login realizado com sucesso', 'user': user.to_dict()}), 200
    else:
        return jsonify({'error': 'Credenciais inválidas'}), 401

@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    user = User.query.get(session['user_id'])
    data = request.json
    
    if data.get('email'):
        # Verificar se email já existe
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Email já cadastrado'}), 400
        user.email = data['email']
    
    if data.get('password'):
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'message': 'Perfil atualizado com sucesso', 'user': user.to_dict()})

@user_bp.route('/balance', methods=['GET'])
@login_required
def get_balance():
    user = User.query.get(session['user_id'])
    return jsonify({'balance': user.balance})

@user_bp.route('/add-balance', methods=['POST'])
@login_required
def add_balance():
    data = request.json
    amount = data.get('amount')
    
    if not amount or amount <= 0:
        return jsonify({'error': 'Valor inválido'}), 400
    
    user = User.query.get(session['user_id'])
    
    # Criar registro de pagamento
    payment = Payment(
        user_id=user.id,
        amount=amount,
        status='pending'
    )
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({
        'message': 'Solicitação de recarga criada',
        'payment_id': payment.id,
        'amount': amount
    })

@user_bp.route('/payments', methods=['GET'])
@login_required
def get_payments():
    user = User.query.get(session['user_id'])
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
    return jsonify([payment.to_dict() for payment in payments])

# Rotas administrativas
@user_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'balance' in data:
        user.balance = float(data['balance'])
    if 'is_admin' in data:
        user.is_admin = bool(data['is_admin'])
    
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
