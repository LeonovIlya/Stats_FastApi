from fastapi import FastAPI

from app.parser.html_parser import get_commands_stats

app = FastAPI()


@app.get('/hello')
def hello():
    return 'Hello'


@app.post("/stats")
async def get_stats():
    data = await get_commands_stats()
    return templates.TemplateResponse(
        'stats.html',
        {'request': request, 'data': data.to_html()})
