# tests/test_api.py - API endpoint tests

import pytest
import json
from src.api import create_app
from src.models import db, User, Class

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        # Create test data
        admin = User(username='testadmin', email='admin@test.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_login_success(client):
    response = client.post('/api/auth/login',
                          json={'username': 'testadmin', 'password': 'admin123'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'access_token' in data
    assert data['user']['role'] == 'admin'

def test_login_failure(client):
    response = client.post('/api/auth/login',
                          json={'username': 'testadmin', 'password': 'wrongpass'})
    assert response.status_code == 401

def test_get_users_unauthorized(client):
    response = client.get('/api/users')
    assert response.status_code == 401

def test_register_user(client):
    # Login first to get token
    login_response = client.post('/api/auth/login',
                                json={'username': 'testadmin', 'password': 'admin123'})
    token = json.loads(login_response.data)['access_token']

    # Register new user
    response = client.post('/api/auth/register',
                          headers={'Authorization': f'Bearer {token}'},
                          json={
                              'username': 'newstudent',
                              'email': 'student@test.com',
                              'password': 'student123',
                              'role': 'student'
                          })
    assert response.status_code == 201

def test_get_classes(client):
    # Login as admin
    login_response = client.post('/api/auth/login',
                                json={'username': 'testadmin', 'password': 'admin123'})
    token = json.loads(login_response.data)['access_token']

    response = client.get('/api/classes',
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert isinstance(json.loads(response.data), list)

if __name__ == '__main__':
    pytest.main([__file__])