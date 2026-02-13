import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test():
    url = os.getenv('REDMINE_URL')
    key = os.getenv('REDMINE_API_KEY')
    
    print(f"URL: {url}")
    print(f"Key: ***{key[-4:]}")
    
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{url}/issues.json",
            headers={'X-Redmine-API-Key': key},
            params={'limit': 1}
        )
        print(f"Status: {r.status_code}")
        print(f"Content: {r.text[:500]}")

asyncio.run(test())
