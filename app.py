from flask import Flask, jsonify, request, Response
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import time
import random

app = Flask(__name__)

http_requests_total = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Tempo de resposta de requisições HTTP em segundos',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1, 1.5, 2, 5, 10)
)

http_errors_total = Counter(
    'http_errors_total',
    'Total de erros HTTP',
    ['method', 'endpoint', 'status_code']
)

books = [
    {"id": "1", "title": "O Senhor dos Anéis", "author": "J.R.R. Tolkien"},
    {"id": "2", "title": "1984", "author": "George Orwell"},
    {"id": "3", "title": "Orgulho e Preconceito", "author": "Jane Austen"},
]

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    end_time = time.time()
    duration = end_time - request.start_time
    method = request.method
    endpoint = request.path
    status_code = response.status_code

    if endpoint == '/metrics':
        return response

    http_requests_total.labels(method, endpoint, status_code).inc()
    http_request_duration_seconds.labels(method, endpoint).observe(duration)

    if status_code >= 400:
        http_errors_total.labels(method, endpoint, status_code).inc()

    return response

@app.route('/health', methods=['GET'])
def health():

    return jsonify({"status": "ok"})

@app.route('/books', methods=['GET'])
def get_books():

    time.sleep(random.uniform(0.05, 0.5))
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():

    data = request.get_json()
    if not data or 'title' not in data or 'author' not in data:
        return jsonify({"message": "Título e autor são obrigatórios."}), 400

    new_book = {
        "id": str(len(books) + 1),
        "title": data['title'],
        "author": data['author']
    }
    books.append(new_book)
    return jsonify({"message": "Livro adicionado com sucesso!", "book": new_book}), 201

@app.route('/metrics')
def metrics():

    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)