import asyncio
import os
import uuid
from datetime import datetime, timezone

import httpx

API=os.environ.get("API_URL","http://localhost:8000")

async def main(n: int = 25):
    async with httpx.AsyncClient(timeout=10) as client:
        for i in range(n):
            payload = {
                "transaction_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "amount": (5 + i % 10) * 10,
                "currency": "USD",
                "merchant_id": f"m_{i%5}",
                "merchant_category": "electronics",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": "web",
                "ip": "127.0.0.1",
                "geo": {"lat": 37.77, "lon": -122.41},
                "device_id": f"dev_{i%3}",
            }
            r = await client.post(f"{API}/transactions", json=payload)
            print(i, r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(main())
