// Global variables
let currentUser = null;
let currentServices = [];
let currentOrders = [];

// API Base URL
const API_BASE = '/api';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Hide loading screen after a short delay
    setTimeout(() => {
        document.getElementById('loading').style.display = 'none';
        checkAuthStatus();
    }, 1000);

    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Auth modal
    setupAuthModal();
    
    // Navigation
    setupNavigation();
    
    // User menu
    setupUserMenu();
    
    // Forms
    setupForms();
    
    // Admin tabs
    setupAdminTabs();
}

function setupAuthModal() {
    const modal = document.getElementById('authModal');
    const closeBtn = modal.querySelector('.close');
    const authTabs = document.querySelectorAll('.auth-tab');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchAuthTab(tabName);
        });
    });
}

function switchAuthTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update forms
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    document.getElementById(`${tabName}Form`).classList.add('active');
}

function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = btn.dataset.page;
            showPage(page);
            
            // Update active nav button
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function setupUserMenu() {
    const userBtn = document.getElementById('userMenuBtn');
    const dropdown = document.getElementById('userDropdown');
    
    userBtn.addEventListener('click', () => {
        dropdown.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
        if (!userBtn.contains(event.target) && !dropdown.contains(event.target)) {
            dropdown.classList.remove('show');
        }
    });
}

function setupForms() {
    // Login form
    document.getElementById('loginFormElement').addEventListener('submit', handleLogin);
    
    // Register form
    document.getElementById('registerFormElement').addEventListener('submit', handleRegister);
    
    // Add balance form
    document.getElementById('addBalanceForm').addEventListener('submit', handleAddBalance);
    
    // Config form
    document.getElementById('configForm').addEventListener('submit', handleConfigSave);
    
    // Service search
    document.getElementById('serviceSearch').addEventListener('input', filterServices);
    
    // Category filter
    document.getElementById('categoryFilter').addEventListener('change', filterServices);
}

function setupAdminTabs() {
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchAdminTab(tabName);
        });
    });
}

function switchAdminTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.admin-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Load content based on tab
    if (tabName === 'users') {
        loadUsers();
    } else if (tabName === 'stats') {
        loadAdminStats();
    }
}

// Authentication functions
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/profile`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            showApp();
            updateUserInfo();
            loadDashboard();
        } else {
            showAuthModal();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showAuthModal();
    }
}

function showAuthModal() {
    document.getElementById('authModal').style.display = 'block';
}

function showApp() {
    document.getElementById('app').style.display = 'flex';
    
    // Show admin nav and page if user is admin
    if (currentUser && currentUser.is_admin) {
        document.querySelector('.admin-only').style.display = 'flex';
        document.getElementById('adminPage').style.display = 'block';
    } else {
        // Hide admin elements for non-admin users
        document.querySelector('.admin-only').style.display = 'none';
        document.getElementById('adminPage').style.display = 'none';
    }
}

function updateUserInfo() {
    if (currentUser) {
        document.getElementById('username').textContent = currentUser.username;
        document.getElementById('userBalance').textContent = `R$ ${currentUser.balance.toFixed(2)}`;
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUser = result.user;
            document.getElementById('authModal').style.display = 'none';
            showApp();
            updateUserInfo();
            loadDashboard();
            showToast('Login realizado com sucesso!', 'success');
        } else {
            showToast(result.error || 'Erro no login', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        username: formData.get('username'),
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Conta criada com sucesso! Faça login.', 'success');
            switchAuthTab('login');
        } else {
            showToast(result.error || 'Erro no registro', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        document.getElementById('app').style.display = 'none';
        showAuthModal();
        showToast('Logout realizado com sucesso!', 'success');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Page navigation
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show selected page
    document.getElementById(`${pageName}Page`).classList.add('active');
    
    // Load page content
    switch (pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'services':
            loadServices();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'payments':
            loadPayments();
            break;
        case 'admin':
            loadAdminConfig();
            break;
    }
}

// Dashboard functions
async function loadDashboard() {
    try {
        // Load user profile to get updated balance
        const profileResponse = await fetch(`${API_BASE}/profile`, {
            credentials: 'include'
        });
        
        if (profileResponse.ok) {
            currentUser = await profileResponse.json();
            updateUserInfo();
        }
        
        // Load orders for stats
        const ordersResponse = await fetch(`${API_BASE}/orders`, {
            credentials: 'include'
        });
        
        if (ordersResponse.ok) {
            const ordersData = await ordersResponse.json();
            currentOrders = ordersData.orders || [];
            updateDashboardStats();
            loadRecentOrders();
        }
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function updateDashboardStats() {
    const totalOrders = currentOrders.length;
    const pendingOrders = currentOrders.filter(order => 
        ['Pending', 'In progress', 'Processing'].includes(order.status)
    ).length;
    const completedOrders = currentOrders.filter(order => 
        order.status === 'Completed'
    ).length;
    const totalSpent = currentOrders.reduce((sum, order) => sum + order.charge, 0);
    
    document.getElementById('totalOrders').textContent = totalOrders;
    document.getElementById('pendingOrders').textContent = pendingOrders;
    document.getElementById('completedOrders').textContent = completedOrders;
    document.getElementById('totalSpent').textContent = `R$ ${totalSpent.toFixed(2)}`;
}

function loadRecentOrders() {
    const recentOrders = currentOrders.slice(0, 5);
    const container = document.getElementById('recentOrdersList');
    
    if (recentOrders.length === 0) {
        container.innerHTML = '<p>Nenhum pedido encontrado.</p>';
        return;
    }
    
    container.innerHTML = recentOrders.map(order => `
        <div class="order-item">
            <div>
                <strong>${order.service_name}</strong><br>
                <small>${order.link}</small>
            </div>
            <div>
                <span class="status-badge status-${order.status.toLowerCase().replace(' ', '-')}">${order.status}</span>
            </div>
            <div>
                R$ ${order.charge.toFixed(2)}
            </div>
        </div>
    `).join('');
}

// Services functions
async function loadServices() {
    try {
        const response = await fetch(`${API_BASE}/services`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            currentServices = await response.json();
            displayServices(currentServices);
            loadCategories();
        } else {
            showToast('Erro ao carregar serviços', 'error');
        }
    } catch (error) {
        console.error('Services load error:', error);
        showToast('Erro de conexão', 'error');
    }
}

function displayServices(services) {
    const container = document.getElementById('servicesList');
    
    if (services.length === 0) {
        container.innerHTML = '<p>Nenhum serviço disponível.</p>';
        return;
    }
    
    container.innerHTML = services.map(service => `
        <div class="service-card">
            <h3>${service.name}</h3>
            <span class="service-type">${service.type}</span>
            <div class="service-price">R$ ${service.final_rate.toFixed(4)}/1000</div>
            <div class="service-range">Min: ${service.min} | Max: ${service.max}</div>
            <button class="btn btn-primary" onclick="openOrderModal(${service.service_id})">
                <i class="fas fa-shopping-cart"></i>
                Fazer Pedido
            </button>
        </div>
    `).join('');
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/services/categories`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const categories = await response.json();
            const select = document.getElementById('categoryFilter');
            
            select.innerHTML = '<option value="">Todas as categorias</option>';
            categories.forEach(category => {
                select.innerHTML += `<option value="${category}">${category}</option>`;
            });
        }
    } catch (error) {
        console.error('Categories load error:', error);
    }
}

function filterServices() {
    const searchTerm = document.getElementById('serviceSearch').value.toLowerCase();
    const selectedCategory = document.getElementById('categoryFilter').value;
    
    let filteredServices = currentServices;
    
    if (searchTerm) {
        filteredServices = filteredServices.filter(service =>
            service.name.toLowerCase().includes(searchTerm) ||
            service.description.toLowerCase().includes(searchTerm)
        );
    }
    
    if (selectedCategory) {
        filteredServices = filteredServices.filter(service =>
            service.category === selectedCategory
        );
    }
    
    displayServices(filteredServices);
}

// Orders functions
async function loadOrders() {
    try {
        const response = await fetch(`${API_BASE}/orders`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            currentOrders = data.orders || [];
            displayOrders(currentOrders);
        } else {
            showToast('Erro ao carregar pedidos', 'error');
        }
    } catch (error) {
        console.error('Orders load error:', error);
        showToast('Erro de conexão', 'error');
    }
}

function displayOrders(orders) {
    const container = document.getElementById('ordersList');
    
    if (orders.length === 0) {
        container.innerHTML = '<p>Nenhum pedido encontrado.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="table-header">
            <div>Serviço</div>
            <div>Link</div>
            <div>Quantidade</div>
            <div>Valor</div>
            <div>Status</div>
            <div>Data</div>
            <div>Ações</div>
        </div>
        ${orders.map(order => `
            <div class="table-row">
                <div>${order.service_name}</div>
                <div><a href="${order.link}" target="_blank">${order.link.substring(0, 30)}...</a></div>
                <div>${order.quantity}</div>
                <div>R$ ${order.charge.toFixed(2)}</div>
                <div><span class="status-badge status-${order.status.toLowerCase().replace(' ', '-')}">${order.status}</span></div>
                <div>${new Date(order.created_at).toLocaleDateString()}</div>
                <div>
                    <button class="btn btn-secondary" onclick="updateOrderStatus(${order.id})">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
            </div>
        `).join('')}
    `;
}

async function updateOrderStatus(orderId) {
    try {
        const response = await fetch(`${API_BASE}/orders/${orderId}/status`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            showToast('Status atualizado', 'success');
            loadOrders();
        } else {
            showToast('Erro ao atualizar status', 'error');
        }
    } catch (error) {
        console.error('Update status error:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function syncOrdersStatus() {
    try {
        const response = await fetch(`${API_BASE}/orders/sync-status`, {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(result.message, 'success');
            loadOrders();
            loadDashboard(); // Update dashboard stats
        } else {
            showToast('Erro ao sincronizar status', 'error');
        }
    } catch (error) {
        console.error('Sync status error:', error);
        showToast('Erro de conexão', 'error');
    }
}

// Payments functions
async function loadPayments() {
    try {
        const response = await fetch(`${API_BASE}/payments`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const payments = await response.json();
            displayPayments(payments);
        } else {
            showToast('Erro ao carregar pagamentos', 'error');
        }
    } catch (error) {
        console.error('Payments load error:', error);
        showToast('Erro de conexão', 'error');
    }
}

function displayPayments(payments) {
    const container = document.getElementById('paymentsList');
    
    if (payments.length === 0) {
        container.innerHTML = '<p>Nenhum pagamento encontrado.</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="table-header">
            <div>ID</div>
            <div>Valor</div>
            <div>Status</div>
            <div>Data</div>
        </div>
        ${payments.map(payment => `
            <div class="table-row">
                <div>#${payment.id}</div>
                <div>R$ ${payment.amount.toFixed(2)}</div>
                <div><span class="status-badge status-${payment.status}">${payment.status}</span></div>
                <div>${new Date(payment.created_at).toLocaleDateString()}</div>
            </div>
        `).join('')}
    `;
}

async function handleAddBalance(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const amountStr = formData.get('amount');
    
    // Validação mais robusta
    if (!amountStr || amountStr.trim() === '') {
        showToast('Por favor, insira um valor', 'error');
        return;
    }
    
    const amount = parseFloat(amountStr.replace(',', '.'));
    
    if (isNaN(amount) || amount <= 0) {
        showToast('Valor inválido. Use apenas números.', 'error');
        return;
    }
    
    if (amount < 1) {
        showToast('Valor mínimo é R$ 1,00', 'error');
        return;
    }
    
    if (amount > 10000) {
        showToast('Valor máximo é R$ 10.000,00', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/payments/create-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ amount: amount })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showPaymentModal(result);
            event.target.reset(); // Limpar formulário
        } else {
            showToast(result.error || 'Erro ao criar pagamento', 'error');
        }
    } catch (error) {
        console.error('Payment creation error:', error);
        showToast(`Erro de conexão: ${error.message}`, 'error');
    }
}

function showPaymentModal(paymentData) {
    const modal = document.getElementById('paymentModal');
    const content = document.getElementById('paymentModalContent');
    
    // Verificar se pix_info existe e tem dados
    const pixInfo = paymentData.pix_info || {};
    const hasQrCode = pixInfo.qr_code && pixInfo.qr_code.length > 0;
    
    content.innerHTML = `
        <h3>Pagamento PIX</h3>
        <p>Valor: R$ ${paymentData.amount.toFixed(2)}</p>
        <p>ID do Pagamento: ${paymentData.payment_id}</p>
        
        ${hasQrCode ? `
            <div class="qr-code">
                <h4>Código PIX:</h4>
                <textarea readonly style="width: 100%; height: 100px;">${pixInfo.qr_code}</textarea>
                <button class="btn btn-secondary" onclick="copyToClipboard('${pixInfo.qr_code}')">
                    <i class="fas fa-copy"></i>
                    Copiar Código PIX
                </button>
            </div>
        ` : `
            <div class="qr-code">
                <h4>Aguardando geração do código PIX...</h4>
                <p>O código PIX será gerado em alguns segundos.</p>
                <button class="btn btn-primary" onclick="checkPaymentStatus(${paymentData.payment_id})">
                    <i class="fas fa-sync"></i>
                    Atualizar
                </button>
            </div>
        `}
        
        <div class="payment-status">
            <p>Status: <span id="paymentStatus">Aguardando pagamento...</span></p>
            <button class="btn btn-primary" onclick="checkPaymentStatus(${paymentData.payment_id})">
                <i class="fas fa-sync"></i>
                Verificar Status
            </button>
        </div>
    `;
    
    modal.style.display = 'block';
    
    // Auto-check payment status every 10 seconds
    const checkInterval = setInterval(() => {
        checkPaymentStatus(paymentData.payment_id, checkInterval);
    }, 10000);
}

async function checkPaymentStatus(paymentId, interval = null) {
    try {
        const response = await fetch(`${API_BASE}/payments/check-payment/${paymentId}`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const result = await response.json();
            document.getElementById('paymentStatus').textContent = result.status;
            
            if (result.status === 'approved') {
                showToast('Pagamento aprovado! Saldo adicionado.', 'success');
                document.getElementById('paymentModal').style.display = 'none';
                updateUserInfo();
                loadPayments();
                if (interval) clearInterval(interval);
            }
        }
    } catch (error) {
        console.error('Payment check error:', error);
    }
}

// Admin functions
async function loadAdminConfig() {
    if (!currentUser || !currentUser.is_admin) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/config`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const config = await response.json();
            populateConfigForm(config);
        }
    } catch (error) {
        console.error('Config load error:', error);
    }
}

function populateConfigForm(config) {
    document.getElementById('baratoApiKey').value = config.barato_api_key || '';
    document.getElementById('profitMargin').value = config.profit_margin || '';
    document.getElementById('mpAccessToken').value = config.mp_access_token || '';
    document.getElementById('mpPublicKey').value = config.mp_public_key || '';
    document.getElementById('mpClientId').value = config.mp_client_id || '';
    document.getElementById('mpClientSecret').value = config.mp_client_secret || '';
}

async function handleConfigSave(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const config = {
        barato_api_key: formData.get('baratoApiKey'),
        profit_margin: formData.get('profitMargin'),
        mp_access_token: formData.get('mpAccessToken'),
        mp_public_key: formData.get('mpPublicKey'),
        mp_client_id: formData.get('mpClientId'),
        mp_client_secret: formData.get('mpClientSecret')
    };
    
    try {
        const response = await fetch(`${API_BASE}/admin/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showToast('Configurações salvas com sucesso!', 'success');
        } else {
            showToast('Erro ao salvar configurações', 'error');
        }
    } catch (error) {
        console.error('Config save error:', error);
        showToast('Erro de conexão', 'error');
    }
}

async function testBaratoAPI() {
    try {
        const response = await fetch(`${API_BASE}/admin/test-barato-api`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast(`API BaratoSocial OK! Saldo: ${result.balance || 'N/A'}`, 'success');
        } else {
            showToast(`Erro na API: ${result.message || result.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('API test error:', error);
        showToast(`Erro de conexão: ${error.message}`, 'error');
    }
}

async function testMercadoPago() {
    try {
        const response = await fetch(`${API_BASE}/admin/test-mercado-pago`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showToast(`Mercado Pago OK! Métodos: ${result.payment_methods_count || 0}`, 'success');
        } else {
            showToast(`Erro no MP: ${result.message || result.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (error) {
        console.error('MP test error:', error);
        showToast(`Erro de conexão: ${error.message}`, 'error');
    }
}

async function loadUsers() {
    if (!currentUser || !currentUser.is_admin) return;
    
    try {
        const response = await fetch(`${API_BASE}/users`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const users = await response.json();
            displayUsers(users);
        }
    } catch (error) {
        console.error('Users load error:', error);
    }
}

function displayUsers(users) {
    const container = document.getElementById('usersList');
    
    container.innerHTML = `
        <div class="table-header">
            <div>ID</div>
            <div>Usuário</div>
            <div>Email</div>
            <div>Saldo</div>
            <div>Admin</div>
            <div>Criado em</div>
        </div>
        ${users.map(user => `
            <div class="table-row">
                <div>${user.id}</div>
                <div>${user.username}</div>
                <div>${user.email}</div>
                <div>R$ ${user.balance.toFixed(2)}</div>
                <div>${user.is_admin ? 'Sim' : 'Não'}</div>
                <div>${new Date(user.created_at).toLocaleDateString()}</div>
            </div>
        `).join('')}
    `;
}

async function loadAdminStats() {
    if (!currentUser || !currentUser.is_admin) return;
    
    try {
        const response = await fetch(`${API_BASE}/admin/dashboard-stats`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const stats = await response.json();
            displayAdminStats(stats);
        }
    } catch (error) {
        console.error('Admin stats load error:', error);
    }
}

function displayAdminStats(stats) {
    const container = document.getElementById('adminStats');
    
    container.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-users"></i></div>
                <div class="stat-info">
                    <h3>${stats.total_users}</h3>
                    <p>Total de Usuários</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-shopping-cart"></i></div>
                <div class="stat-info">
                    <h3>${stats.total_orders}</h3>
                    <p>Total de Pedidos</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-dollar-sign"></i></div>
                <div class="stat-info">
                    <h3>R$ ${stats.total_revenue.toFixed(2)}</h3>
                    <p>Receita Total</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-calendar"></i></div>
                <div class="stat-info">
                    <h3>R$ ${stats.monthly_revenue.toFixed(2)}</h3>
                    <p>Receita do Mês</p>
                </div>
            </div>
        </div>
    `;
}

// Order modal functions
function openOrderModal(serviceId) {
    const service = currentServices.find(s => s.service_id === serviceId);
    if (!service) return;
    
    const modal = document.getElementById('orderModal');
    const content = document.getElementById('orderModalContent');
    
    content.innerHTML = `
        <h3>Fazer Pedido - ${service.name}</h3>
        <p><strong>Preço:</strong> R$ ${service.final_rate.toFixed(4)} por 1000</p>
        <p><strong>Mín:</strong> ${service.min} | <strong>Máx:</strong> ${service.max}</p>
        
        <form id="orderForm">
            <input type="hidden" name="service_id" value="${service.service_id}">
            
            <div class="form-group">
                <label for="orderLink">Link/URL</label>
                <input type="url" id="orderLink" name="link" required>
            </div>
            
            <div class="form-group">
                <label for="orderQuantity">Quantidade</label>
                <input type="number" id="orderQuantity" name="quantity" min="${service.min}" max="${service.max}" required>
            </div>
            
            <div class="form-group">
                <label for="orderComments">Comentários (opcional)</label>
                <textarea id="orderComments" name="comments" rows="3"></textarea>
            </div>
            
            <div class="order-total">
                <p>Total estimado: <span id="orderTotal">R$ 0,00</span></p>
            </div>
            
            <button type="submit" class="btn btn-primary">
                <i class="fas fa-shopping-cart"></i>
                Fazer Pedido
            </button>
        </form>
    `;
    
    // Setup quantity change listener
    document.getElementById('orderQuantity').addEventListener('input', function() {
        const quantity = parseInt(this.value) || 0;
        const total = (service.final_rate * quantity) / 1000;
        document.getElementById('orderTotal').textContent = `R$ ${total.toFixed(2)}`;
    });
    
    // Setup form submission
    document.getElementById('orderForm').addEventListener('submit', handleOrderSubmit);
    
    modal.style.display = 'block';
}

async function handleOrderSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        service_id: parseInt(formData.get('service_id')),
        link: formData.get('link'),
        quantity: parseInt(formData.get('quantity')),
        comments: formData.get('comments')
    };
    
    try {
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Pedido criado com sucesso!', 'success');
            document.getElementById('orderModal').style.display = 'none';
            updateUserInfo(); // Update balance
            loadOrders();
        } else {
            showToast(result.error || 'Erro ao criar pedido', 'error');
        }
    } catch (error) {
        console.error('Order creation error:', error);
        showToast('Erro de conexão', 'error');
    }
}

// Utility functions
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Remove toast after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Código copiado para a área de transferência!', 'success');
    }).catch(() => {
        showToast('Erro ao copiar código', 'error');
    });
}

function showProfile() {
    // TODO: Implement profile modal
    showToast('Funcionalidade em desenvolvimento', 'info');
}

// Close modals when clicking close button
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('close')) {
        event.target.closest('.modal').style.display = 'none';
    }
});

