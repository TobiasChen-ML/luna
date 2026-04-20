import logging
from typing import Optional, Any, Callable
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, select, update, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from ..core.config import get_settings
from ..models.user import User as UserModel

logger = logging.getLogger(__name__)


class DatabaseService:
    _engine = None
    _session_local = None
    
    def __init__(self):
        self.settings = get_settings()
        self._init_db()
    
    def _init_db(self):
        if DatabaseService._engine is None:
            DatabaseService._engine = create_engine(
                self.settings.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in self.settings.database_url else {},
                poolclass=StaticPool if "sqlite" in self.settings.database_url else None,
                echo=self.settings.debug
            )
            DatabaseService._session_local = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=DatabaseService._engine,
                expire_on_commit=False
            )
    
    def get_session(self) -> Session:
        return DatabaseService._session_local()
    
    @contextmanager
    def transaction(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def run_in_transaction(self, func: Callable[[Session], Any]) -> Any:
        with self.transaction() as session:
            return func(session)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        with self.transaction() as session:
            return session.query(UserModel).filter(UserModel.id == user_id).first()
    
    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        with self.transaction() as session:
            user = session.query(UserModel).filter(UserModel.email == email).first()
            if user:
                session.expunge(user)
            return user
    
    async def create_user(self, user_id: str, email: str, display_name: Optional[str] = None) -> UserModel:
        with self.transaction() as session:
            user = UserModel(
                id=user_id,
                email=email,
                display_name=display_name
            )
            session.add(user)
            session.flush()
            session.refresh(user)
            session.expunge(user)
            return user
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[UserModel]:
        with self.transaction() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.flush()
                session.refresh(user)
                return user
            return None
    
    async def update_user_credits(self, user_id: int, amount: int) -> Optional[UserModel]:
        with self.transaction() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                user.credits += amount
                if amount > 0:
                    user.total_credits_earned += amount
                else:
                    user.total_credits_spent += abs(amount)
                session.flush()
                session.refresh(user)
                return user
            return None
    
    async def deduct_credits_by_user_id(
        self, 
        user_id: str, 
        amount: float
    ) -> tuple[bool, float, str]:
        """
        Deduct credits from user by user_id.
        Returns (success, remaining_credits, error_message).
        """
        with self.transaction() as session:
            user = session.query(UserModel).filter(
                UserModel.id == user_id
            ).first()
            
            if not user:
                return False, 0, "User not found"
            
            if user.credits < amount:
                return False, user.credits, "Insufficient credits"
            
            user.credits -= amount
            user.total_credits_spent += abs(amount)
            session.flush()
            session.refresh(user)
            
            return True, user.credits, ""
    
    async def update_last_checkin(self, user_id: int) -> Optional[UserModel]:
        with self.transaction() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                user.last_checkin_at = datetime.utcnow()
                session.flush()
                session.refresh(user)
                return user
            return None
    
    async def delete_user(self, user_id: int) -> bool:
        with self.transaction() as session:
            user = session.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                session.delete(user)
                return True
            return False
    
    async def list_users(self, page: int = 1, page_size: int = 20) -> tuple[list[UserModel], int]:
        with self.get_session() as session:
            query = session.query(UserModel)
            total = query.count()
            users = query.offset((page - 1) * page_size).limit(page_size).all()
            return users, total