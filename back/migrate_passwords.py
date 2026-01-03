"""
Скрипт для миграции существующих паролей в зашифрованный формат.
Запускать один раз после обновления.
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from app.core.database import db_manager
from app.models.user import User
from app.utils.encryption import encryption


async def migrate_passwords():
    """Шифрует все незашифрованные пароли"""
    
    async with db_manager.async_session_master() as db:
        # Получаем всех пользователей
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        migrated = 0
        
        for user in users:
            updated = False
            
            # Шифруем SMTP пароль если не зашифрован
            if user.smtp_password and not user.smtp_password.startswith('enc:'):
                user.smtp_password = encryption.encrypt(user.smtp_password)
                updated = True
                print(f"Encrypted SMTP password for {user.email}")
            
            # Шифруем IMAP пароль если не зашифрован
            if user.imap_password and not user.imap_password.startswith('enc:'):
                user.imap_password = encryption.encrypt(user.imap_password)
                updated = True
                print(f"Encrypted IMAP password for {user.email}")
            
            if updated:
                migrated += 1
        
        await db.commit()
        print(f"\nMigration complete. Encrypted passwords for {migrated} users.")


if __name__ == "__main__":
    asyncio.run(migrate_passwords())
