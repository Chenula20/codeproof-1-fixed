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
        resp = await client.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json={
                'model': 'anthropic/claude-sonnet-5.5',
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'max_tokens': 10,
            }
        )
        print(f'Status: {resp.status_code}')
        print(f'Response: {resp.text}')

asyncio.run(test())