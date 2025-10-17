import asyncio
from surrealdb import AsyncSurreal
from utils.config import settings

async def test():
    url = settings.SURREALDB_URL
    user = settings.SURREALDB_USER
    password = settings.SURREALDB_PASS
    ns = getattr(settings, 'SURREALDB_NS', None)
    db = getattr(settings, 'SURREALDB_DB', None)

    print('Connecting to', url)
    client = AsyncSurreal(url)
    try:
        await client.connect()
        print('Connected')
        await client.signin({
            'username': user,
            'password': password,
            'namespace': ns
        })
        print('Signed in')
        if ns and db:
            await client.use(ns, db)
            print('Using', ns, db)
        # run a simple query
        res = await client.query('SELECT 1')
        print('Query result:', res)
        await client.close()
        print('Closed')
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    asyncio.run(test())
