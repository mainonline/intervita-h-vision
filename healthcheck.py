from aiohttp import web

async def health_check(request):
    return web.Response(text="OK")

app = web.Application()
app.add_routes([web.get('/health', health_check)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8081)