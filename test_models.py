import httpx
import asyncio

async def test():
    headers = {
        'Authorization': 'Bearer sk-or-your-openrouter-key-here',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://codeproof.app',
        'X-Title': 'CodeProof',
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get('https://openrouter.ai/api/v1/models', headers=headers)
        print(f'Status: {resp.status_code}')
        import json
        data = resp.json()
        for model in data.get('data', [])[:15]:
            print(f'  {model["id"]}')

asyncio.run(test())