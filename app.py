from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Configurações do aplicativo
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("postgresql://postgres:REdtIyMRHdAwvikUYcPFrLYKkwlOCfzV@yamanote.proxy.rlwy.net:30349/railway")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'sua_chave_secreta_super_segura_aqui'  # Altere para uma chave segura em produção

# Extensões permitidas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'psd', 'ai'}

db = SQLAlchemy(app)

# Decorator para verificar login e permissões
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if role and session.get('user_role') != role:
                flash('Acesso não autorizado.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modelos de dados
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='client')  # 'client', 'social_media' ou 'admin'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relações explícitas
    projects_as_client = db.relationship('Project', foreign_keys='Project.client_id', backref='client_user', lazy=True)
    projects_as_social_media = db.relationship('Project', foreign_keys='Project.social_media_id', backref='social_media_user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='draft')  # 'draft', 'submitted', 'in_review', 'approved', 'rejected', 'revision'
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    social_media_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    
    # Relações
    posts = db.relationship('Post', backref='project', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    platform = db.Column(db.String(50))  # Instagram, Facebook, etc.
    status = db.Column(db.String(20), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    media = db.relationship('Media', backref='post', lazy=True)
    feedbacks = db.relationship(
        'Feedback', 
        backref='post', 
        lazy=True,
        foreign_keys='Feedback.post_id'  # especifica claramente a chave
    )

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='comment')  # 'comment', 'approved', 'rejected', 'revision'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos para resposta do feedback
    response = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    response_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))  # Post criado em resposta
    
    # Relação com o post de resposta
    response_post = db.relationship('Post', foreign_keys=[response_post_id])

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if check_password_hash(user.password, password):
                # Verificar se o usuário está ativo/aprovado
                if user.role == 'client' and user.status != 'approved':
                    flash('Sua conta ainda não foi aprovada. Entre em contato com o administrador.', 'warning')
                    return render_template('login.html')
                
                # Verificar se o usuário foi rejeitado
                if user.status == 'rejected':
                    flash('Sua conta foi rejeitada. Entre em contato com o administrador para mais informações.', 'danger')
                    return render_template('login.html')
                
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_role'] = user.role
                
                if user.role == 'client':
                    return redirect(url_for('client_dashboard'))
                elif user.role == 'social_media':
                    return redirect(url_for('social_media_dashboard'))
                else:
                    return redirect(url_for('admin_dashboard'))
            else:
                flash('Senha incorreta.', 'danger')
        else:
            flash('Email não encontrado.', 'danger')
    
    return render_template('login.html')

# Rota para visualizar e gerenciar clientes (apenas social media e admin)
@app.route('/clients')
@login_required()
def view_clients():
    if session['user_role'] not in ['social_media', 'admin']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))
    
    clients = User.query.filter_by(role='client').order_by(User.created_at.desc()).all()
    return render_template('clients.html', clients=clients)

# Rota para editar status do cliente (apenas social media e admin)
@app.route('/edit-client-status/<int:client_id>', methods=['POST'])
@login_required()
def edit_client_status(client_id):
    if session['user_role'] not in ['social_media', 'admin']:
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    client = User.query.get_or_404(client_id)
    if client.role != 'client':
        return jsonify({'error': 'Usuário não é um cliente'}), 400
    
    new_status = request.form.get('status')
    if new_status not in ['pending', 'approved', 'rejected']:
        return jsonify({'error': 'Status inválido'}), 400
    
    client.status = new_status
    db.session.commit()
    
    flash(f'Status do cliente {client.name} atualizado para {new_status}.', 'success')
    return redirect(url_for('view_clients'))

# Rota para editar informações do cliente (apenas social media e admin)
@app.route('/edit-client/<int:client_id>', methods=['POST'])
@login_required()
def edit_client(client_id):
    if session['user_role'] not in ['social_media', 'admin']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))
    
    client = User.query.get_or_404(client_id)
    if client.role != 'client':
        flash('Usuário não é um cliente.', 'danger')
        return redirect(url_for('view_clients'))
    
    client.name = request.form.get('name')
    client.email = request.form.get('email')
    client.company = request.form.get('company')
    client.phone = request.form.get('phone')
    
    db.session.commit()
    
    flash(f'Informações do cliente {client.name} atualizadas com sucesso.', 'success')
    return redirect(url_for('view_clients'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'danger')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(
            name=name,
            email=email,
            phone=phone,
            company=company,
            password=hashed_password,
            role='client',
            status='pending'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Aguarde a aprovação da sua conta.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

# Painéis de usuário
@app.route('/client/dashboard')
@login_required('client')
def client_dashboard():
    user = User.query.get(session['user_id'])
    projects = user.projects_as_client
    
    # Organizar projetos por status
    projects_by_status = {
        'in_review': [p for p in projects if p.status == 'in_review'],
        'approved': [p for p in projects if p.status == 'approved'],
        'rejected': [p for p in projects if p.status == 'rejected'],
        'revision': [p for p in projects if p.status == 'revision'],
        'submitted': [p for p in projects if p.status == 'submitted'],
    }
    
    return render_template('client-dashboard.html', 
                          user=user, 
                          projects=projects,
                          projects_by_status=projects_by_status)

@app.route('/social-media/dashboard')
@login_required('social_media')
def social_media_dashboard():
    user = User.query.get(session['user_id'])
    
    # Buscar todos os projetos atribuídos a este social media
    projects = user.projects_as_social_media
    
    # Organizar projetos por status
    projects_by_status = {
        'draft': [p for p in projects if p.status == 'draft'],
        'submitted': [p for p in projects if p.status == 'submitted'],
        'in_review': [p for p in projects if p.status == 'in_review'],
        'approved': [p for p in projects if p.status == 'approved'],
        'rejected': [p for p in projects if p.status == 'rejected'],
        'revision': [p for p in projects if p.status == 'revision'],
    }
    
    # Buscar usuários clientes pendentes de aprovação
    pending_clients = User.query.filter_by(role='client', status='pending').all()
    
    return render_template('social-media-dashboard.html', 
                          user=user, 
                          projects=projects,
                          projects_by_status=projects_by_status,
                          pending_clients=pending_clients)

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    # Estatísticas para o dashboard admin
    users_count = User.query.count()
    active_projects_count = Project.query.filter(Project.status.in_(['draft', 'submitted', 'in_review', 'revision'])).count()
    posts_count = Post.query.count()
    pending_clients_count = User.query.filter_by(role='client', status='pending').count()
    projects_in_progress_count = Project.query.filter(Project.status.in_(['draft', 'submitted', 'in_review', 'revision'])).count()
    completed_projects_count = Project.query.filter(Project.status.in_(['approved', 'rejected'])).count()
    media_files_count = Media.query.count()
    
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    return render_template('admin-dashboard.html', 
                         users_count=users_count,
                         active_projects_count=active_projects_count,
                         posts_count=posts_count,
                         pending_clients_count=pending_clients_count,
                         recent_projects=recent_projects,
                         projects_in_progress_count=projects_in_progress_count,
                         completed_projects_count=completed_projects_count,
                         media_files_count=media_files_count)

# Rotas para gerenciamento de clientes (apenas social media e admin)
@app.route('/approve-client/<int:client_id>')
@login_required('social_media')
def approve_client(client_id):
    client = User.query.get_or_404(client_id)
    if client.role != 'client' or client.status != 'pending':
        flash('Cliente inválido para aprovação.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    client.status = 'approved'
    db.session.commit()
    
    flash(f'Cliente {client.name} aprovado com sucesso.', 'success')
    return redirect(url_for('social_media_dashboard'))

@app.route('/reject-client/<int:client_id>')
@login_required('social_media')
def reject_client(client_id):
    client = User.query.get_or_404(client_id)
    if client.role != 'client' or client.status != 'pending':
        flash('Cliente inválido para rejeição.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    client.status = 'rejected'
    db.session.commit()
    
    flash(f'Cliente {client.name} rejeitado.', 'info')
    return redirect(url_for('social_media_dashboard'))

# Rotas para gerenciamento de projetos
@app.route('/create-project', methods=['GET', 'POST'])
@login_required('social_media')
def create_project():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        client_id = request.form.get('client_id')
        deadline = request.form.get('deadline')
        
        if not all([title, description, client_id]):
            flash('Preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('create_project'))
        
        # Verificar se o cliente existe e está aprovado
        client = User.query.get(client_id)
        if not client or client.role != 'client' or client.status != 'approved':
            flash('Cliente inválido ou não aprovado.', 'danger')
            return redirect(url_for('create_project'))
        
        # Converter a data de deadline
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None
        
        new_project = Project(
            title=title,
            description=description,
            client_id=client_id,
            social_media_id=session['user_id'],
            status='draft',
            deadline=deadline_date
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=new_project.id))
    
    # Buscar clientes aprovados para o formulário
    clients = User.query.filter_by(role='client', status='approved').all()
    return render_template('create-project.html', clients=clients)

@app.route('/download/<int:media_id>')
@login_required('client')
def download_file(media_id):
    try:
        media = db.session.get(Media, media_id)
        if not media:
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('client_dashboard'))

        post = db.session.get(Post, media.post_id)
        if not post:
            flash('Post não encontrado.', 'danger')
            return redirect(url_for('client_dashboard'))

        project = db.session.get(Project, post.project_id)
        if not project:
            flash('Projeto não encontrado.', 'danger')
            return redirect(url_for('client_dashboard'))

        # Permissão: o cliente logado deve ser dono do projeto
        if project.client_id != session.get('user_id'):
            flash('Acesso não autorizado.', 'danger')
            return redirect(url_for('client_dashboard'))

        # Caminho absoluto e seguro
        upload_root = os.path.realpath(app.config['UPLOAD_FOLDER'])
        filename = secure_filename(media.filename)
        file_path = os.path.realpath(os.path.join(upload_root, filename))

        # Path traversal guard
        if not file_path.startswith(upload_root + os.sep):
            flash('Acesso não autorizado.', 'danger')
            return redirect(url_for('client_dashboard'))

        # Arquivo existe?
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'danger')
            return redirect(url_for('view_project', project_id=project.id))

        # Download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        # Logar o erro ajuda muito no debug local
        print('[download_file] erro:', repr(e))
        flash('Erro ao baixar o arquivo.', 'danger')
        return redirect(url_for('client_dashboard'))

@app.route('/project/<int:project_id>')
@login_required()
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = session['user_id']
    user_role = session['user_role']
    
    # Verificar permissões
    if user_role == 'client' and project.client_id != user_id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    if user_role == 'social_media' and project.social_media_id != user_id:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    return render_template('view-project.html', project=project)

@app.route('/project/<int:project_id>/create-post', methods=['GET', 'POST'])
@login_required('social_media')
def create_post(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Verificar se o social media tem permissão para este projeto
    if project.social_media_id != session['user_id']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        platform = request.form.get('platform')
        
        if not title:
            flash('Título é obrigatório.', 'danger')
            return redirect(url_for('create_post', project_id=project_id))
        
        new_post = Post(
            project_id=project_id,
            title=title,
            description=description,
            platform=platform,
            status='draft'
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        # Processar uploads de arquivos
        if 'media_files' in request.files:
            files = request.files.getlist('media_files')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Criar pasta de uploads se não existir
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    # Obter tipo do arquivo
                    file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
                    
                    new_media = Media(
                        post_id=new_post.id,
                        filename=filename,
                        file_type=file_type
                    )
                    db.session.add(new_media)
        
        db.session.commit()
        flash('Post criado com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    
    return render_template('create-post.html', project=project)

# Rota para deletar post (apenas social media dono do projeto)
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required('social_media')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    project = Project.query.get_or_404(post.project_id)
    
    # Verificar se o social media tem permissão para este projeto
    if project.social_media_id != session['user_id']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    try:
        # Deletar mídias associadas ao post
        for media in post.media:
            # Remover arquivo físico
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], media.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.delete(media)
        
        # Deletar feedbacks associados ao post
        for feedback in post.feedbacks:
            db.session.delete(feedback)
        
        # Deletar o post
        db.session.delete(post)
        db.session.commit()
        
        flash('Post deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao deletar o post.', 'danger')
        app.logger.error(f"Erro ao deletar post: {str(e)}")
    
    return redirect(url_for('view_project', project_id=project.id))

# Rota para responder feedback criando novo post - CORRIGIDA
@app.route('/feedback/<int:feedback_id>/respond', methods=['GET', 'POST'])
@login_required('social_media')
def respond_to_feedback(feedback_id):  # Recebe feedback_id, não post_id
    feedback = Feedback.query.get_or_404(feedback_id)
    post = Post.query.get_or_404(feedback.post_id)
    project = Project.query.get_or_404(post.project_id)
    
    # Verificar se o social media tem permissão para este projeto
    if project.social_media_id != session['user_id']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        copy_media = request.form.get('copy_media') == 'on'
        
        if not title:
            flash('Título é obrigatório.', 'danger')
            return render_template('respond-feedback.html', 
                                 feedback=feedback, 
                                 post=post, 
                                 project=project)
        
        # Criar novo post baseado no feedback
        new_post = Post(
            project_id=project.id,
            title=title,
            description=description,
            platform=post.platform,
            status='draft'
        )
        
        db.session.add(new_post)
        db.session.flush()  # Para obter o ID do novo post
        
        # Copiar mídias do post original se solicitado
        if copy_media:
            for media in post.media:
                new_media = Media(
                    post_id=new_post.id,
                    filename=media.filename,
                    file_type=media.file_type
                )
                db.session.add(new_media)
        
        # Marcar o feedback como respondido
        feedback.response = f"Respondido com novo post: #{new_post.id}"
        feedback.responded_at = datetime.utcnow()
        feedback.response_post_id = new_post.id
        
        db.session.commit()
        
        flash('Resposta ao feedback criada com sucesso!', 'success')
        return redirect(url_for('view_project', project_id=project.id))  # Corrigido para redirecionar para o projeto
    
    # Gerar título sugestivo baseado no feedback
    suggested_title = f"Revisão - {post.title}"
    if feedback.status == 'revision':
        suggested_title = f"Revisão - {post.title}"
    elif feedback.status == 'rejected':
        suggested_title = f"Nova versão - {post.title}"
    
    return render_template('respond-feedback.html', 
                         feedback=feedback, 
                         post=post, 
                         project=project,
                         suggested_title=suggested_title)

@app.route('/post/<int:post_id>/submit')
@login_required('social_media')
def submit_post(post_id):
    post = Post.query.get_or_404(post_id)
    project = Project.query.get_or_404(post.project_id)
    
    # Verificar permissões
    if project.social_media_id != session['user_id']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('social_media_dashboard'))
    
    post.status = 'submitted'
    project.status = 'submitted'
    db.session.commit()
    
    flash('Post enviado para aprovação!', 'success')
    return redirect(url_for('view_project', project_id=project.id))

@app.route('/post/<int:post_id>/feedback', methods=['POST'])
@login_required('client')
def add_feedback(post_id):
    post = Post.query.get_or_404(post_id)
    project = Project.query.get_or_404(post.project_id)
    
    # Verificar se o cliente tem permissão para este projeto
    if project.client_id != session['user_id']:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('client_dashboard'))
    
    comment = request.form.get('comment')
    status = request.form.get('status')
    
    if not comment:
        flash('Comentário é obrigatório.', 'danger')
        return redirect(url_for('view_project', project_id=project.id))
    
    new_feedback = Feedback(
        post_id=post_id,
        user_id=session['user_id'],
        comment=comment,
        status=status
    )
    
    # Atualizar status do post e projeto
    if status in ['approved', 'rejected']:
        post.status = status
        project.status = status
    elif status == 'revision':
        post.status = 'revision'
        project.status = 'revision'
    
    db.session.add(new_feedback)
    db.session.commit()
    
    flash('Feedback enviado com sucesso!', 'success')
    return redirect(url_for('view_project', project_id=project.id))

# Inicialização do banco de dados
def init_db():
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        if not User.query.filter_by(role='admin').first():
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(
                name='Administrador',
                email='admin@falcondigital.com',
                password=hashed_password,
                role='admin',
                status='approved',
                company='Falcon Digital Solutions'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Usuário admin criado: admin@falcondigital.com / admin123")
        
        # Criar usuário social media padrão se não existir
        if not User.query.filter_by(role='social_media').first():
            hashed_password = generate_password_hash('social123', method='pbkdf2:sha256')
            social_user = User(
                name='Social Media',
                email='social@falcondigital.com',
                password=hashed_password,
                role='social_media',
                status='approved',
                company='Falcon Digital Solutions'
            )
            db.session.add(social_user)
            db.session.commit()
            print("Usuário social media criado: social@falcondigital.com / social123")

init_db()

if __name__ == '__main__':
    app.run(debug=True)








