import pytest

from handlers.admin import orders
from utils import router


class RecordingBot:
    def __init__(self):
        self.messages = []
        self.photos = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})
        return True

    async def send_photo(self, chat_id, photo, caption=None, **kwargs):
        self.photos.append(
            {"chat_id": chat_id, "photo": photo, "caption": caption, "kwargs": kwargs}
        )
        return True


class FailingBot:
    async def send_message(self, *args, **kwargs):
        raise RuntimeError("telegram unavailable")

    async def send_photo(self, *args, **kwargs):
        raise RuntimeError("telegram unavailable")


def _order_data(order_id="ORDER_TEST"):
    return {
        "order_id": order_id,
        "documents": [
            {
                "type": "sanepid",
                "quantity": 1,
                "items": [{"full_name": "Test User"}],
            }
        ],
        "delivery": None,
        "payment_method": "blik",
        "total_price": 150,
        "user": {"id": 123, "username": "testuser"},
    }


@pytest.fixture(autouse=True)
def clean_orders():
    orders.clear()
    yield
    orders.clear()


@pytest.mark.asyncio
async def test_send_order_to_manager_routes_message_and_stores_admin_metadata(
    monkeypatch,
):
    monkeypatch.setattr(router, "ROUTING", {"sanepid": 111, "default": 999})
    bot = RecordingBot()

    target = await router.send_order_to_manager(
        bot=bot,
        order_data=_order_data(),
        user_id=123,
        payment_proof_file_id="proof-file-id",
    )

    assert target == 111
    assert bot.photos[0]["chat_id"] == 111
    assert bot.photos[0]["photo"] == "proof-file-id"
    assert bot.photos[0]["kwargs"]["reply_markup"] is not None
    assert bot.messages[0]["chat_id"] == 111
    assert "ORDER_TEST" in bot.messages[0]["text"]
    assert orders["ORDER_TEST"]["user_id"] == 123
    assert orders["ORDER_TEST"]["total_price"] == 150


@pytest.mark.asyncio
async def test_send_order_to_manager_keeps_order_metadata_when_telegram_fails(
    monkeypatch,
):
    monkeypatch.setattr(router, "ROUTING", {"sanepid": 111, "default": 999})

    target = await router.send_order_to_manager(
        bot=FailingBot(),
        order_data=_order_data("ORDER_FAILING_SEND"),
        user_id=456,
        payment_proof_file_id=None,
    )

    assert target == 111
    assert orders["ORDER_FAILING_SEND"]["user_id"] == 456
