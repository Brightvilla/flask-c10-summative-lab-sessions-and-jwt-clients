from flask import request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from config import app, db
from models import User, Note

api = Api(app)


class Signup(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        password_confirmation = data.get("password_confirmation", "")

        if not username or not password:
            return {"error": "Username and password are required."}, 422
        if password != password_confirmation:
            return {"error": "Passwords do not match."}, 422
        if User.query.filter_by(username=username).first():
            return {"error": "Username already taken."}, 422

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=user.id)
        return {"token": token, "user": user.to_dict()}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(username=data.get("username", "")).first()

        if not user or not user.check_password(data.get("password", "")):
            return {"error": "Invalid username or password."}, 401

        token = create_access_token(identity=user.id)
        return {"token": token, "user": user.to_dict()}, 200


class Me(Resource):
    @jwt_required()
    def get(self):
        user = db.session.get(User, get_jwt_identity())
        if not user:
            return {"error": "User not found."}, 404
        return user.to_dict(), 200


class NoteList(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        pagination = (
            Note.query.filter_by(user_id=user_id)
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "notes": [n.to_dict() for n in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": pagination.page,
        }, 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        title = data.get("title", "").strip()
        body = data.get("body", "").strip()

        if not title or not body:
            return {"error": "Title and body are required."}, 422

        note = Note(title=title, body=body, user_id=user_id)
        db.session.add(note)
        db.session.commit()
        return note.to_dict(), 201


class NoteDetail(Resource):
    def _get_owned_note(self, note_id):
        user_id = get_jwt_identity()
        note = db.session.get(Note, note_id)
        if not note:
            return None, ({"error": "Note not found."}, 404)
        if note.user_id != user_id:
            return None, ({"error": "Forbidden."}, 403)
        return note, None

    @jwt_required()
    def get(self, note_id):
        note, err = self._get_owned_note(note_id)
        if err:
            return err
        return note.to_dict(), 200

    @jwt_required()
    def patch(self, note_id):
        note, err = self._get_owned_note(note_id)
        if err:
            return err
        data = request.get_json()
        if "title" in data:
            note.title = data["title"].strip()
        if "body" in data:
            note.body = data["body"].strip()
        db.session.commit()
        return note.to_dict(), 200

    @jwt_required()
    def delete(self, note_id):
        note, err = self._get_owned_note(note_id)
        if err:
            return err
        db.session.delete(note)
        db.session.commit()
        return {}, 204


api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(Me, "/me")
api.add_resource(NoteList, "/notes")
api.add_resource(NoteDetail, "/notes/<int:note_id>")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
