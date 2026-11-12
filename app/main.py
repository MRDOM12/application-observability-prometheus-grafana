from flask import Flask, Response, request, g
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)
import time

app = Flask(__name__)

# Total HTTP requests
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

# Requests currently being processed
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active HTTP requests"
)

# HTTP request latency
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"]
)


@app.before_request
def before_request():
    if request.path != "/metrics":
        g.start_time = time.time()
        ACTIVE_CONNECTIONS.inc()


@app.after_request
def after_request(response):
    if request.path != "/metrics":
        elapsed = time.time() - g.start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            endpoint=request.path
        ).observe(elapsed)

        ACTIVE_CONNECTIONS.dec()

    return response


@app.route("/")
def home():
    return {
        "message": "Application is running",
        "status": "healthy"
    }, 200


@app.route("/slow")
def slow():
    time.sleep(3)
    return {"message": "Slow response completed"}, 200


@app.route("/error")
def error():
    return {"message": "Simulated internal server error"}, 500


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
