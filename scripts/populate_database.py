import random
from datetime import datetime, timedelta

from app.db import get_db
from app.schemas import BookingStatus, PermissionAction
from app.core.auth import get_password_hash
from app.db.models import (
    UserModel, GroupModel, ResourceModel, PermissionModel,
    BookingModel
)


def populate_db():

    db = next(get_db())

    # 1. Create superuser
    admin_user = UserModel(
        email="admin1@company.com",
        username="admin1",
        hashed_password=get_password_hash(password="password#1"),
        is_active=True,
        is_superuser=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)


    # 2. Create common users
    users = []
    for i in range(5):
        user = UserModel(
            email=f"user{i}@company.com",
            username=f"user{i}",
            hashed_password=get_password_hash(password="password#1"),
            is_active=True,
            is_superuser=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        users.append(user)


    # 3. Create groups
    groups = []
    group_names = ["Developers", "Managers", "HR", "Sales", "Support"]
    for name in group_names:
        group = GroupModel(
            name=name,
            description=f"Group for {name.lower()}"
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        groups.append(group)


    # 4. Add users to groups
    for user in users:
        selected_groups = random.sample(groups, random.randint(1, 3))
        user.groups.extend(selected_groups)
    db.commit()

    # 5. Create resources
    resources = []
    resource_data = [
        {"name": "Meeting Room A", "description": "Small meeting room", "capacity": 1},
        {"name": "Meeting Room B", "description": "Large meeting room", "capacity": 2},
        {"name": "Projector", "description": "Portable projector", "capacity": 1},
        {"name": "Development Server", "description": "Server for development", "capacity": 5},
        {"name": "Production Server", "description": "Server for production", "capacity": 3}
    ]

    for data in resource_data:
        resource = ResourceModel(**data)
        db.add(resource)
        db.commit()
        db.refresh(resource)
        resources.append(resource)


    # 6. Create permissions
    # Every group gets random resource
    for group in groups:
        selected_resources = random.sample(resources, random.randint(2, 3))
        for resource in selected_resources:
            # Allow view permission for all groups
            view_permission = PermissionModel(
                action=PermissionAction.VIEW,
                group_id=group.id,
                resource_id=resource.id
            )
            db.add(view_permission)

            # Some groups get booking permissions
            if random.random() > 0.3:  # 70% chance
                book_permission = PermissionModel(
                    action=PermissionAction.BOOK,
                    group_id=group.id,
                    resource_id=resource.id
                )
                db.add(book_permission)

    # 7. Some users get direct permissions
    for user in users:
        selected_resources = random.sample(resources, random.randint(1, 2))
        for resource in selected_resources:
            if random.random() > 0.5:
                permission = PermissionModel(
                    action=PermissionAction.VIEW,
                    user_id=user.id,
                    resource_id=resource.id
                )
                db.add(permission)

            if random.random() > 0.7:
                permission = PermissionModel(
                    action=PermissionAction.BOOK,
                    user_id=user.id,
                    resource_id=resource.id
                )
                db.add(permission)

    # 8. Create test bookings
    now = datetime.now()
    for _ in range(10):

        user = random.choice(users)
        resource = random.choice(resources)

        days_offset = random.randint(1, 30)
        start_time = now + timedelta(days=days_offset, hours=random.randint(9, 16))
        end_time = start_time + timedelta(hours=random.randint(1, 3))

        booking = BookingModel(
            user_id=user.id,
            resource_id=resource.id,
            start_time=start_time,
            end_time=end_time,
            booking_status=random.choice(list(BookingStatus.__members__.values()))
        )
        db.add(booking)

    db.commit()
    print("Database populated successfully!")


if __name__ == "__main__":
    populate_db()