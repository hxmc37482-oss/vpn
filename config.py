# Конфигурация MartVPN бота

BOT_TOKEN = "8942107106:AAHClbAFqzp4_qyk2EpI-EgWwnSPOpPaLfQ"

# Токен CryptoBot (Crypto Pay API), получается через @CryptoBot -> Crypto Pay -> Create App
CRYPTO_PAY_TOKEN = "610353:AAXNJ9gALJWfcUliajBklBgwXr7cdxWNs4p"

PRICE_ASSET = "USDT"  # актив в котором принимаем оплату через CryptoBot

# Тарифы: id -> данные тарифа
PLANS = {
    "day": {
        "title": "24 часа",
        "amount": 0.5,
        "emoji": "⏱",
        "description": "Доступ на 24 часа",
    },
    "forever": {
        "title": "Навсегда",
        "amount": 1.0,
        "emoji": "♾",
        "description": "Безлимитный доступ навсегда",
    },
}

# VLESS / подписка ключ, который бот выдает после оплаты
VLESS_KEY = "https://omorkovka.ru/sub/40381742-b7ca-49f5-ab6d-8c9a2f7dcb50"

# Путь к баннеру для приветственного сообщения (положи картинку сюда)
BANNER_PATH = "banner/welcome.jpg"

# Файл где хранится история платежей (простая json база)
DB_PATH = "payments.json"

# API CryptoBot
CRYPTO_PAY_API_URL = "https://pay.crypt.bot/api"
