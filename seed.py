from faker import Faker
from server import create_app, db
from server.models import User, Note

fake = Faker()
app = create_app()


def seed():
    with app.app_context():
        print("Clearing existing data...")
        Note.query.delete()
        User.query.delete()
        db.session.commit()

        print("Seeding users...")
        users = []
        for _ in range(3):
            user = User(username=fake.unique.user_name())
            user.password_hash = "password123"
            db.session.add(user)
            users.append(user)
        db.session.commit()

        print("Seeding notes...")
        categories = ["work", "personal", "ideas", "general"]
        for user in users:
            for _ in range(5):
                note = Note(
                    title=fake.sentence(nb_words=4).rstrip("."),
                    content=fake.paragraph(nb_sentences=3),
                    category=fake.random_element(categories),
                    user_id=user.id,
                )
                db.session.add(note)
        db.session.commit()

        print(f"Done! Seeded {len(users)} users and {len(users) * 5} notes.")


if __name__ == "__main__":
    seed()
