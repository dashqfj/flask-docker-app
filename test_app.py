import pytest
from app import app, db, User, cache
import time
import json

@pytest.fixture(scope='session')
def client():
    app.config['TESTING'] = True
    
    # Ждем, пока база данных будет готова
    time.sleep(3)
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_create_user(client):
    """Тест создания пользователя"""
    response = client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    assert response.status_code == 200
    assert b'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u0441\u043e\u0437\u0434\u0430\u043d' in response.data

def test_get_users(client):
    """Тест получения списка пользователей"""
    # Создаем тестового пользователя
    client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    
    # Получаем список пользователей
    response = client.get('/users')
    assert response.status_code == 200
    assert b'testuser' in response.data
    assert b'test@test.com' in response.data

def test_get_user(client):
    """Тест получения конкретного пользователя"""
    # Создаем пользователя
    client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    
    # Получаем пользователя
    response = client.get('/users/1')
    assert response.status_code == 200
    assert b'testuser' in response.data

def test_update_user(client):
    """Тест обновления пользователя"""
    client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    response = client.put('/users/1', 
        json={'username': 'updated_user'})
    assert response.status_code == 200
    assert b'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d' in response.data

def test_delete_user(client):
    """Тест удаления пользователя"""
    client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    response = client.delete('/users/1')
    assert response.status_code == 200
    assert b'\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c \u0443\u0441\u043f\u0435\u0448\u043d\u043e \u0443\u0434\u0430\u043b\u0435\u043d' in response.data

def test_cache_functionality(client):
    """Тест функциональности кэширования"""
    # Создаем пользователя
    client.post('/users', 
        json={'username': 'testuser', 'email': 'test@test.com'})
    
    # Первый запрос (сохранится в кэш)
    response1 = client.get('/users/1')
    
    # Второй запрос (должен взяться из кэша)
    response2 = client.get('/users/1')
    
    assert response1.data == response2.data
    
    # Проверяем очистку кэша
    response = client.delete('/users/1/cache')
    assert response.status_code == 200