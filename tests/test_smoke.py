from bot.config import get_settings


def test_settings_load():
    settings = get_settings()
    assert settings is not None
