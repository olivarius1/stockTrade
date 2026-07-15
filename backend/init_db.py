from app.db import init_db
from app.db.session import SessionLocal
from app.db.models import User
from app.core.security import get_password_hash

def main():
    init_db()
    db = SessionLocal()

    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            hashed_password=get_password_hash("admin123")
        )
        db.add(admin)
        db.commit()
        print("Admin user created")

    db.close()

if __name__ == "__main__":
    main()
