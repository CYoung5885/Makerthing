import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)

# -------------------------------
# CONFIG
# -------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///makerthing.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')

db = SQLAlchemy(app)

# -------------------------------
# MODELS
# -------------------------------
class Page(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False, default='Untitled')
    blocks = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'blocks': self.blocks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

# -------------------------------
# ROUTES — UI
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/page/<page_id>")
def edit_page(page_id):
    return render_template("index.html")  # Frontend handles routing

# -------------------------------
# ROUTES — API
# -------------------------------
@app.route("/api/pages", methods=["GET"])
def list_pages():
    pages = Page.query.order_by(Page.updated_at.desc()).all()
    return jsonify([p.to_dict() for p in pages])

@app.route("/api/pages", methods=["POST"])
def create_page():
    data = request.get_json()
    page = Page(
        title=data.get('title', 'Untitled'),
        blocks=data.get('blocks', [])
    )
    db.session.add(page)
    db.session.commit()
    return jsonify(page.to_dict()), 201

@app.route("/api/pages/<page_id>", methods=["GET"])
def get_page(page_id):
    page = db.get_or_404(Page, page_id)
    return jsonify(page.to_dict())

@app.route("/api/pages/<page_id>", methods=["PUT"])
def update_page(page_id):
    page = db.get_or_404(Page, page_id)
    data = request.get_json()
    if 'title' in data:
        page.title = data['title']
    if 'blocks' in data:
        page.blocks = data['blocks']
    db.session.commit()
    return jsonify(page.to_dict())

@app.route("/api/pages/<page_id>", methods=["DELETE"])
def delete_page(page_id):
    page = db.get_or_404(Page, page_id)
    db.session.delete(page)
    db.session.commit()
    return '', 204

@app.route("/api/pages/<page_id>/export", methods=["GET"])
def export_page(page_id):
    page = db.get_or_404(Page, page_id)
    html = render_template("export.html", page=page)
    return html, 200, {
        'Content-Type': 'text/html',
        'Content-Disposition': f'attachment; filename="{page.title}.html"'
    }

# -------------------------------
# INIT DB + RUN
# -------------------------------
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)