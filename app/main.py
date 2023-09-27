from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.parser.html_parser import get_commands_stats, get_levels

app = FastAPI()

app.mount("/static", StaticFiles(directory="./app/static"), name="static")

templates = Jinja2Templates(directory="./app/templates")


@app.get('/hello')
def hello():
    return 'Hello'


@app.get('/stats', response_class=HTMLResponse)
async def get_stats(request: Request):
    data = await get_commands_stats()
    levels = await get_levels()
    return templates.TemplateResponse(
        'stats.html',
        {'request': request,
         'data': data,
         'levels': levels})
