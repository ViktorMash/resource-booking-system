from app.db import get_db
from app.db.models import UserModel, GroupModel, ResourceModel, PermissionModel, BookingModel
from sqlalchemy.orm import Session


def clear_db():
    """
    Clears all tables in the database.
    Deletion happens in an order that respects foreign key constraints.
    """
    db = next(get_db())

    # Clear tables in the correct order to avoid foreign key constraint errors
    clear_bookings(db)
    clear_permissions(db)
    clear_user_group_associations(db)
    clear_resources(db)
    clear_groups(db)
    clear_users(db)

    print("Database successfully cleared!")


def clear_bookings(db: Session):
    db.query(BookingModel).delete()
    db.commit()
    print("Bookings table cleared")


def clear_permissions(db: Session):
    db.query(PermissionModel).delete()
    db.commit()
    print("Permissions table cleared")


def clear_user_group_associations(db: Session):
    """Clears associations between users and groups"""
    # Get all users
    users = db.query(UserModel).all()

    # For each user, clear the groups list
    for user in users:
        user.groups = []

    db.commit()
    print("User-group associations cleared")


def clear_resources(db: Session):
    db.query(ResourceModel).delete()
    db.commit()
    print("Resources table cleared")


def clear_groups(db: Session):
    db.query(GroupModel).delete()
    db.commit()
    print("Groups table cleared")


def clear_users(db: Session):
    db.query(UserModel).delete()
    db.commit()
    print("Users table cleared")


if __name__ == "__main__":
    clear_db()