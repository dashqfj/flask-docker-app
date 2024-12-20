from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
import os
import socket

app = Flask(__name__)

# Конфигурация в зависимости от окружения
if os.getenv('FLASK_ENV') == 'testing':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/flask_db_test'
    app.config['TESTING'] = True
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/flask_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Конфигурация Redis кэша
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOST', 'redis')
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = f"redis://{app.config['CACHE_REDIS_HOST']}:{app.config['CACHE_REDIS_PORT']}/0"

# Инициализация расширений
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Создание пользователя
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(username=data['username'], email=data['email'])
    try:
        db.session.add(new_user)
        db.session.commit()
        cache.delete('all_users')
        return jsonify({'message': 'Пользователь успешно создан'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Получение всех пользователей с кэшированием
@app.route('/users', methods=['GET'])
@cache.cached(timeout=300, key_prefix='all_users')  # Кэшируем на 5 минут
def get_users():
    users = User.query.all()
    users_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]
    return jsonify(users_list)

# Получение конкретного пользователя с кэшированием
@app.route('/users/<int:id>', methods=['GET'])
@cache.memoize(300)  # Кэшируем на 5 минут
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

# Обновление пользователя
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    data = request.get_json()
    try:
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        db.session.commit()
        cache.delete('all_users')
        cache.delete_memoized(get_user, id)
        return jsonify({'message': 'Пользователь успешно обновлен'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Удаление пользователя
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'Пользователь не найден'}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        cache.delete('all_users')
        cache.delete_memoized(get_user, id)
        return jsonify({'message': 'Пользователь успешно удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Очистка кэша для конкретного пользователя
@app.route('/users/<int:id>/cache', methods=['DELETE'])
def clear_user_cache(id):
    cache.delete_memoized(get_user, id)
    return jsonify({'message': f'Кэш для пол��зователя {id} очищен'})

@app.route('/')
def index():
    hostname = socket.gethostname()
    return jsonify({
        'message': 'Flask API работает',
        'container_id': hostname
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0') 