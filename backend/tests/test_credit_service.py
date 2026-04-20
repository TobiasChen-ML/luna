import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.user import User
from app.models.credit_transaction import CreditTransaction
from app.models.credit_config import CreditCostConfig
from app.models.credit_pack import CreditPack
from app.services.credit_service import CreditService, InsufficientCreditsError


@pytest.fixture
def test_db_engine():
    engine = create_engine("sqlite:///:memory:")
    from app.models.user import Base as UserBase
    from app.models.credit_config import Base as ConfigBase
    
    UserBase.metadata.create_all(engine)
    ConfigBase.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def mock_db_service(test_db_session):
    mock = MagicMock()
    
    class TransactionContext:
        def __enter__(self):
            return test_db_session
        def __exit__(self, *args):
            test_db_session.commit()
    
    mock.transaction = lambda: TransactionContext()
    mock.get_session = lambda: test_db_session
    
    return mock


@pytest.fixture
def mock_redis_service():
    redis = MagicMock()
    redis.get_json = AsyncMock(return_value=None)
    redis.set_json = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def credit_service(mock_db_service, mock_redis_service):
    return CreditService(db=mock_db_service, redis=mock_redis_service)


@pytest.fixture
def credit_service_no_cache(mock_db_service):
    redis = MagicMock()
    redis.get_json = AsyncMock(return_value=None)
    redis.set_json = AsyncMock(return_value=True)
    return CreditService(db=mock_db_service, redis=redis)


@pytest.fixture
def test_user(test_db_session):
    user = User(
        id="test_user_001",
        email="test@example.com",
        credits=10.0,
        monthly_credits=5.0,
        purchased_credits=5.0,
        signup_bonus_granted=False,
        tier="free",
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def premium_user(test_db_session):
    user = User(
        id="premium_user_001",
        email="premium@example.com",
        credits=100.0,
        monthly_credits=50.0,
        purchased_credits=50.0,
        signup_bonus_granted=True,
        tier="premium",
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


@pytest.fixture
def credit_config(test_db_session):
    config = CreditCostConfig(
        message_cost=0.1,
        voice_cost=0.2,
        image_cost=2,
        video_cost=4,
        voice_call_per_minute=3,
        signup_bonus_credits=10,
        premium_monthly_credits=100,
    )
    test_db_session.add(config)
    test_db_session.commit()
    return config


class TestBalanceCache:
    async def test_get_balance_cache_hit(self, mock_db_service, mock_redis_service, test_user):
        cached_balance = {
            "total": 100.0,
            "purchased": 50.0,
            "monthly": 50.0,
            "subscription_tier": "premium",
            "subscription_period": "1m",
            "subscription_end": None,
            "signup_bonus_granted": True,
        }
        mock_redis_service.get_json = AsyncMock(return_value=cached_balance)
        
        service = CreditService(db=mock_db_service, redis=mock_redis_service)
        balance = await service.get_balance("test_user_001")
        
        assert balance["total"] == 100.0
        assert balance["subscription_tier"] == "premium"
        mock_redis_service.get_json.assert_called_once()
    
    async def test_get_balance_cache_miss_queries_db(self, credit_service, test_user, test_db_session, mock_redis_service):
        mock_redis_service.get_json = AsyncMock(return_value=None)
        
        balance = await credit_service.get_balance(test_user.id)
        
        assert balance["total"] == 10.0
        mock_redis_service.get_json.assert_called_once()
        mock_redis_service.set_json.assert_called_once()
    
    async def test_get_balance_redis_failure_falls_back_to_db(self, mock_db_service, mock_redis_service, test_user):
        mock_redis_service.get_json = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        service = CreditService(db=mock_db_service, redis=mock_redis_service)
        balance = await service.get_balance(test_user.id)
        
        assert balance["total"] == 10.0
    
    async def test_deduct_credits_updates_cache(self, credit_service, test_user, test_db_session, mock_redis_service):
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=3.0,
            usage_type="message"
        )
        
        mock_redis_service.set_json.assert_called()
        call_args = mock_redis_service.set_json.call_args
        assert "user:balance:test_user_001" in call_args[0][0]
    
    async def test_add_credits_updates_cache(self, credit_service, test_user, test_db_session, mock_redis_service):
        await credit_service.add_credits(
            user_id=test_user.id,
            amount=50.0,
            transaction_type="purchase",
            credit_source="purchased"
        )
        
        mock_redis_service.set_json.assert_called()
    
    async def test_refund_credits_updates_cache(self, credit_service, test_user, test_db_session, mock_redis_service):
        await credit_service.refund_credits(
            user_id=test_user.id,
            amount=5.0,
            original_transaction_id="tx_001",
            reason="Test refund"
        )
        
        mock_redis_service.set_json.assert_called()
    
    async def test_admin_adjust_updates_cache(self, credit_service, test_user, test_db_session, mock_redis_service):
        await credit_service.admin_adjust_credits(
            user_id=test_user.id,
            amount=50.0,
            description="Test",
            admin_email="admin@test.com"
        )
        
        mock_redis_service.set_json.assert_called()
    
    async def test_cache_key_format(self, credit_service, test_user):
        key = credit_service._get_balance_cache_key(test_user.id)
        assert key == "user:balance:test_user_001"


class TestGetBalance:
    async def test_get_balance_existing_user(self, credit_service, test_user, test_db_session):
        balance = await credit_service.get_balance(test_user.id)
        assert balance["total"] == 10.0
        assert balance["monthly"] == 5.0
        assert balance["purchased"] == 5.0
        assert balance["subscription_tier"] == "free"

    async def test_get_balance_nonexistent_user(self, credit_service):
        balance = await credit_service.get_balance("nonexistent_user")
        assert balance["total"] == 0.0
        assert balance["subscription_tier"] == "free"


class TestDeductCredits:
    async def test_deduct_from_monthly_first(self, credit_service, test_user, test_db_session):
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=3.0,
            usage_type="message"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.monthly_credits == 2.0
        assert test_user.purchased_credits == 5.0
        assert test_user.credits == 7.0

    async def test_deduct_monthly_exhausted_then_purchased(self, credit_service, test_user, test_db_session):
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=7.0,
            usage_type="message"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.monthly_credits == 0.0
        assert test_user.purchased_credits == 3.0
        assert test_user.credits == 3.0

    async def test_deduct_insufficient_raises(self, credit_service, test_user):
        with pytest.raises(InsufficientCreditsError):
            await credit_service.deduct_credits(
                user_id=test_user.id,
                amount=100.0,
                usage_type="image"
            )

    async def test_deduct_creates_transaction(self, credit_service, test_user, test_db_session):
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=2.0,
            usage_type="image",
            character_id="char_001",
            session_id="session_001"
        )
        
        tx = test_db_session.query(CreditTransaction).filter(
            CreditTransaction.user_id == test_user.id,
            CreditTransaction.usage_type == "image"
        ).first()
        
        assert tx is not None
        assert tx.amount == -2.0
        assert tx.character_id == "char_001"


class TestAddCredits:
    async def test_add_purchased_credits(self, credit_service, test_user, test_db_session):
        await credit_service.add_credits(
            user_id=test_user.id,
            amount=50.0,
            transaction_type="purchase",
            credit_source="purchased",
            order_id="order_001"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.purchased_credits == 55.0
        assert test_user.credits == 60.0

    async def test_add_monthly_credits(self, credit_service, test_user, test_db_session):
        await credit_service.add_credits(
            user_id=test_user.id,
            amount=20.0,
            transaction_type="subscription",
            credit_source="monthly"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.monthly_credits == 25.0
        assert test_user.credits == 30.0

    async def test_add_nonexistent_user_raises(self, credit_service):
        with pytest.raises(ValueError):
            await credit_service.add_credits(
                user_id="nonexistent",
                amount=10.0,
                transaction_type="purchase"
            )


class TestGrantSignupBonus:
    async def test_grant_signup_bonus_success(self, credit_service, test_user, test_db_session, credit_config):
        result = await credit_service.grant_signup_bonus(test_user.id)
        assert result is True
        
        test_db_session.refresh(test_user)
        assert test_user.signup_bonus_granted is True
        assert test_user.purchased_credits == 15.0

    async def test_grant_signup_bonus_idempotent(self, credit_service, test_user, test_db_session, credit_config):
        await credit_service.grant_signup_bonus(test_user.id)
        result = await credit_service.grant_signup_bonus(test_user.id)
        assert result is False
        
        test_db_session.refresh(test_user)
        assert test_user.purchased_credits == 15.0

    async def test_grant_signup_bonus_nonexistent_user(self, credit_service):
        with pytest.raises(ValueError):
            await credit_service.grant_signup_bonus("nonexistent")


class TestGrantMonthlyCredits:
    async def test_grant_to_premium_user(self, credit_service, premium_user, test_db_session, credit_config):
        result = await credit_service.grant_monthly_credits(premium_user.id)
        assert result is True
        
        test_db_session.refresh(premium_user)
        assert premium_user.monthly_credits == 150.0
        assert premium_user.last_monthly_credit_grant is not None

    async def test_grant_to_free_user_skipped(self, credit_service, test_user):
        result = await credit_service.grant_monthly_credits(test_user.id)
        assert result is False

    async def test_grant_too_soon_skipped(self, credit_service, premium_user, test_db_session, credit_config):
        premium_user.last_monthly_credit_grant = datetime.utcnow() - timedelta(days=10)
        test_db_session.commit()
        
        result = await credit_service.grant_monthly_credits(premium_user.id)
        assert result is False

    async def test_grant_after_28_days(self, credit_service, premium_user, test_db_session, credit_config):
        premium_user.last_monthly_credit_grant = datetime.utcnow() - timedelta(days=29)
        test_db_session.commit()
        
        result = await credit_service.grant_monthly_credits(premium_user.id)
        assert result is True
        
        test_db_session.refresh(premium_user)
        assert premium_user.monthly_credits == 150.0


class TestRefundCredits:
    async def test_refund_success(self, credit_service, test_user, test_db_session):
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=5.0,
            usage_type="image",
            order_id="tx_001"
        )
        
        test_db_session.refresh(test_user)
        balance_after_deduct = test_user.credits
        
        result = await credit_service.refund_credits(
            user_id=test_user.id,
            amount=5.0,
            original_transaction_id="tx_001",
            reason="Image generation failed"
        )
        assert result is True
        
        test_db_session.refresh(test_user)
        assert test_user.credits == balance_after_deduct + 5.0

    async def test_refund_duplicate_prevented(self, credit_service, test_user, test_db_session):
        await credit_service.refund_credits(
            user_id=test_user.id,
            amount=5.0,
            original_transaction_id="tx_001",
            reason="Refund 1"
        )
        
        with pytest.raises(ValueError, match="Already refunded"):
            await credit_service.refund_credits(
                user_id=test_user.id,
                amount=5.0,
                original_transaction_id="tx_001",
                reason="Refund 2"
            )

    async def test_refund_nonexistent_user(self, credit_service):
        with pytest.raises(ValueError, match="not found"):
            await credit_service.refund_credits(
                user_id="nonexistent",
                amount=5.0,
                original_transaction_id="tx_001",
                reason="Test"
            )


class TestAdminAdjustCredits:
    async def test_adjust_add_credits(self, credit_service, test_user, test_db_session):
        await credit_service.admin_adjust_credits(
            user_id=test_user.id,
            amount=50.0,
            description="Compensation",
            admin_email="admin@test.com"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.purchased_credits == 55.0
        assert test_user.credits == 60.0

    async def test_adjust_deduct_credits(self, credit_service, test_user, test_db_session):
        await credit_service.admin_adjust_credits(
            user_id=test_user.id,
            amount=-3.0,
            description="Penalty",
            admin_email="admin@test.com"
        )
        
        test_db_session.refresh(test_user)
        assert test_user.credits == 7.0

    async def test_adjust_over_deduct_fails(self, credit_service, test_user):
        with pytest.raises(InsufficientCreditsError):
            await credit_service.admin_adjust_credits(
                user_id=test_user.id,
                amount=-100.0,
                description="Too much",
                admin_email="admin@test.com"
            )

    async def test_adjust_user_not_found(self, credit_service):
        with pytest.raises(ValueError, match="not found"):
            await credit_service.admin_adjust_credits(
                user_id="nonexistent",
                amount=10.0,
                description="Test",
                admin_email="admin@test.com"
            )


class TestGetTransactions:
    async def test_get_transactions(self, credit_service, test_user, test_db_session):
        await credit_service.add_credits(
            user_id=test_user.id,
            amount=10.0,
            transaction_type="purchase"
        )
        await credit_service.deduct_credits(
            user_id=test_user.id,
            amount=5.0,
            usage_type="message"
        )
        
        txs = await credit_service.get_transactions(test_user.id, limit=10)
        assert len(txs) == 2

    async def test_get_transactions_pagination(self, credit_service, test_user, test_db_session):
        for i in range(5):
            await credit_service.add_credits(
                user_id=test_user.id,
                amount=1.0,
                transaction_type="purchase"
            )
        
        txs = await credit_service.get_transactions(test_user.id, limit=2, offset=0)
        assert len(txs) == 2