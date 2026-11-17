from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from main import create_app


def client():
    directory = TemporaryDirectory()
    app = create_app(Path(directory.name) / "test.db")
    testing = TestClient(app)
    testing.__enter__()
    return directory, testing


def sample(name="Andrea", rating=5, comment="Excelente atención de la tienda."):
    return dict(user_name=name, rating=rating, comment=comment)


def test_create_and_date():
    d, c = client()
    try:
        r = c.post('/api/reviews', json=sample()); assert r.status_code == 201
        data = r.json(); assert data['published_at'] and data['user_name'] == 'Andrea'
    finally: c.__exit__(None, None, None); d.cleanup()


def test_stats_count_changes():
    d, c = client()
    try:
        assert c.get('/api/reviews/stats').json()['total_comments'] == 0
        c.post('/api/reviews', json=sample())
        c.post('/api/reviews', json=sample(name="Juan", rating=4))
        stats = c.get('/api/reviews/stats').json()
        assert stats['total_comments'] == 2 and stats['average_rating'] == 4.5
    finally: c.__exit__(None, None, None); d.cleanup()


def test_rating_limits():
    d, c = client()
    try:
        assert c.post('/api/reviews', json=sample(rating=0)).status_code == 422
        assert c.post('/api/reviews', json=sample(rating=6)).status_code == 422
    finally: c.__exit__(None, None, None); d.cleanup()


def test_short_comment_accepted():
    d, c = client()
    try: assert c.post('/api/reviews', json=sample(comment="malo")).status_code == 201
    finally: c.__exit__(None, None, None); d.cleanup()


def test_reply_and_visibility():
    d, c = client()
    try:
        rid = c.post('/api/reviews', json=sample()).json()['id']
        r = c.patch(f'/api/reviews/{rid}/reply', json={'response':'Gracias por su reseña'})
        assert r.json()['replied_at'] is not None
        r = c.patch(f'/api/reviews/{rid}/visibility', json={'visible':False})
        assert r.json()['visible'] is False
        stats = c.get('/api/reviews/stats').json()
        assert stats['hidden_comments'] == 1 and stats['answered_comments'] == 1
    finally: c.__exit__(None, None, None); d.cleanup()


def test_delete_reduces_count():
    d, c = client()
    try:
        rid = c.post('/api/reviews', json=sample()).json()['id']
        assert c.delete(f'/api/reviews/{rid}').status_code == 204
        assert c.get('/api/reviews/stats').json()['total_comments'] == 0
    finally: c.__exit__(None, None, None); d.cleanup()
