import uuid
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from config import Config
from bomber import sms_bomber, call_bomber, attack_manager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── Database Models ───────────────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class AttackLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target = db.Column(db.String(20), nullable=False)
    attack_type = db.Column(db.String(20), nullable=False)  # sms, call, combined
    count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')

with app.app_context():
    db.create_all()
    # Create default admin if not exists
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── Routes ────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # In production, use check_password_hash
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    active_attacks = attack_manager.get_active_attacks()
    logs = AttackLog.query.filter_by(user_id=current_user.id).order_by(AttackLog.timestamp.desc()).limit(20).all()
    return render_template('dashboard.html', 
                         active_attacks=active_attacks, 
                         logs=logs,
                         sms_services=sms_bomber.get_available_services(),
                         call_services=call_bomber.get_available_services())

@app.route('/api/attack/start', methods=['POST'])
@login_required
def start_attack():
    data = request.get_json()
    target = data.get('target', '').strip()
    attack_type = data.get('type', 'sms')
    count = int(data.get('count', 5))
    delay = float(data.get('delay', Config.DEFAULT_DELAY_SECONDS))
    message = data.get('message', 'Security test alert')
    
    # Validate phone number
    if not target or len(target) < 10:
        return jsonify({'success': False, 'error': 'Invalid phone number'}), 400
    
    if count < 1 or count > Config.MAX_BURST:
        return jsonify({'success': False, 'error': f'Count must be between 1 and {Config.MAX_BURST}'}), 400
    
    attack_id = str(uuid.uuid4())[:8]
    
    if attack_type == 'sms':
        attack_manager.start_sms_attack(attack_id, target, count, delay, sms_bomber, message)
    elif attack_type == 'call':
        attack_manager.start_call_attack(attack_id, target, count, delay, call_bomber, message)
    else:  # combined
        attack_manager.start_combined_attack(attack_id, target, count, delay, sms_bomber, call_bomber, message)
    
    # Log the attack
    log = AttackLog(
        user_id=current_user.id,
        target=target,
        attack_type=attack_type,
        count=count,
        status='running'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'attack_id': attack_id})

@app.route('/api/attack/stop', methods=['POST'])
@login_required
def stop_attack():
    data = request.get_json()
    attack_id = data.get('attack_id', '')
    
    if attack_manager.stop_attack(attack_id):
        return jsonify({'success': True, 'message': 'Attack stopped'})
    
    return jsonify({'success': False, 'error': 'Attack not found'}), 404

@app.route('/api/attack/status', methods=['GET'])
@login_required
def attack_status():
    return jsonify({
        'active_attacks': list(attack_manager.get_active_attacks().keys())
    })

@app.route('/api/logs', methods=['GET'])
@login_required
def get_logs():
    logs = AttackLog.query.filter_by(user_id=current_user.id).order_by(AttackLog.timestamp.desc()).limit(50).all()
    return jsonify([{
        'id': l.id,
        'target': l.target,
        'type': l.attack_type,
        'count': l.count,
        'timestamp': l.timestamp.isoformat(),
        'status': l.status
    } for l in logs])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
