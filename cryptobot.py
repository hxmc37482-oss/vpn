import aiohttp
from config import CRYPTO_PAY_TOKEN, CRYPTO_PAY_API_URL, PRICE_ASSET


HEADERS = {"Crypto-Pay-API-Token": CRYPTO_PAY_TOKEN}


async def create_invoice(amount: float, description: str = "Доступ к MartVPN"):
    """Создает инвойс в CryptoBot и возвращает (invoice_id, pay_url)."""
    payload = {
        "asset": PRICE_ASSET,
        "amount": str(amount),
        "description": description,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{CRYPTO_PAY_API_URL}/createInvoice", headers=HEADERS, json=payload
        ) as resp:
            data = await resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"CryptoBot createInvoice error: {data}")

    result = data["result"]
    return result["invoice_id"], result["pay_url"]


async def get_invoice_status(invoice_id: str) -> str:
    """Возвращает статус инвойса: active / paid / expired."""
    params = {"invoice_ids": str(invoice_id)}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{CRYPTO_PAY_API_URL}/getInvoices", headers=HEADERS, params=params
        ) as resp:
            data = await resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"CryptoBot getInvoices error: {data}")

    items = data["result"]["items"]
    if not items:
        return "unknown"
    return items[0]["status"]
