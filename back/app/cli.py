"""CLI commands for database management"""
import asyncio
from sqlalchemy import select
from app.core.database import db_manager
from app.core.security import security
from app.models.user import User, UserRole
import sys


async def create_admin_user(username: str, email: str, password: str):
    """Create admin user"""
    async for session in db_manager.get_session():
        # Check if user exists
        result = await session.execute(select(User).where(User.username == username))
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"User {username} already exists")
            return
        
        user = User(
            username=username,
            email=email,
            password_hash=security.get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            full_name="System Administrator"
        )
        
        session.add(user)
        await session.commit()
        print(f"Admin user {username} created successfully")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create_admin":
        if len(sys.argv) != 5:
            print("Usage: python -m app.cli create_admin <username> <email> <password>")
            sys.exit(1)
        
        asyncio.run(create_admin_user(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print(f"Unknown command: {command}")
