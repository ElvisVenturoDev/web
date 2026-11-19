from app import create_app
from app.config import get_port
from werkzeug.middleware.proxy_fix import ProxyFix

app = create_app()

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


if __name__ == "__main__":
    port = get_port()
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )