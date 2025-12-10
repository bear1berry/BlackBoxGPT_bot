from bot.storage.models import User, UserMode


def test_user_model_basic():
    u = User(
        telegram_id=123,
        username="test",
        mode=UserMode.UNIVERSAL,
    )
    assert u.telegram_id == 123
