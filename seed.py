from faker import Faker
from config import app, db
from models import User, Note

fake = Faker()


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        users = []
        for _ in range(5):
            user = User(username=fake.unique.user_name())
            user.set_password("password123")
            db.session.add(user)
            users.append(user)

        db.session.commit()

        for user in users:
            for _ in range(6):
                note = Note(
                    title=fake.sentence(nb_words=5),
                    body=fake.paragraph(nb_sentences=3),
                    user_id=user.id,
                )
                db.session.add(note)

        db.session.commit()
        print(f"Seeded {len(users)} users with 6 notes each.")


if __name__ == "__main__":
    seed()
