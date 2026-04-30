from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import db
from .models import User, Note


def register_routes(app):

    @app.route("/signup", methods=["POST"])
    def signup():
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        password_confirmation = data.get("password_confirmation", "")

        errors = []
        if not username:
            errors.append("Username is required.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if not password:
            errors.append("Password is required.")
        if password != password_confirmation:
            errors.append("Passwords do not match.")
        if errors:
            return jsonify({"errors": errors}), 422

        user = User(username=username)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "user": user.to_dict()}), 201

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
        user = User.query.filter_by(username=data.get("username", "")).first()

        if not user or not user.authenticate(data.get("password", "")):
            return jsonify({"errors": ["Invalid username or password."]}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "user": user.to_dict()}), 200

    @app.route("/me", methods=["GET"])
    @jwt_required()
    def me():
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({"errors": ["User not found."]}), 404
        return jsonify(user.to_dict()), 200

    # Notes CRUD

    @app.route("/notes", methods=["GET"])
    @jwt_required()
    def get_notes():
        user_id = int(get_jwt_identity())
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        pagination = (
            Note.query.filter_by(user_id=user_id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

        return jsonify({
            "notes": [n.to_dict() for n in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
        }), 200

    @app.route("/notes", methods=["POST"])
    @jwt_required()
    def create_note():
        user_id = int(get_jwt_identity())
        data = request.get_json()

        errors = []
        if not data.get("title", "").strip():
            errors.append("Title is required.")
        if not data.get("content", "").strip():
            errors.append("Content is required.")
        if errors:
            return jsonify({"errors": errors}), 422

        note = Note(
            title=data["title"].strip(),
            content=data["content"].strip(),
            category=data.get("category", "general"),
            user_id=user_id,
        )
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    @app.route("/notes/<int:note_id>", methods=["GET"])
    @jwt_required()
    def get_note(note_id):
        user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if not note:
            return jsonify({"errors": ["Note not found."]}), 404
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["PATCH"])
    @jwt_required()
    def update_note(note_id):
        user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if not note:
            return jsonify({"errors": ["Note not found."]}), 404

        data = request.get_json()
        if "title" in data:
            note.title = data["title"].strip()
        if "content" in data:
            note.content = data["content"].strip()
        if "category" in data:
            note.category = data["category"]

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["DELETE"])
    @jwt_required()
    def delete_note(note_id):
        user_id = int(get_jwt_identity())
        note = Note.query.filter_by(id=note_id, user_id=user_id).first()
        if not note:
            return jsonify({"errors": ["Note not found."]}), 404

        db.session.delete(note)
        db.session.commit()
        return jsonify({}), 200
