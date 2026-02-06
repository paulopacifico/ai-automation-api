from __future__ import annotations

import os

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User, UserRole


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        raise SystemExit("ADMIN_EMAIL and ADMIN_PASSWORD must be set")

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
            )
            db.add(user)
        else:
            user.role = UserRole.ADMIN
            user.hashed_password = hash_password(password)

        db.commit()

    print("Admin user ready")


if __name__ == "__main__":
    main()
