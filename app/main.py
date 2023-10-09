from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Annotated
from aiohttp.client_exceptions import ClientConnectorError
from app.parsers.html_parser import check_url, get_game_name_link, parse_stats

app = FastAPI()

app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")

app.add_middleware(SessionMiddleware,
                   secret_key="your-secret-key",
                   max_age=3600)


@app.get('/', response_class=HTMLResponse)
async def get_index(request: Request):
    request.session['url'] = None
    request.session['selected_levels'] = None
    return templates.TemplateResponse(
        'index.html',
        {'request': request})


@app.post('/', response_class=HTMLResponse)
async def send_url(request: Request,
                   url: Annotated[str, Form()]):
    request.session['url'] = url
    return RedirectResponse(url='/stats', status_code=303)


@app.get('/stats', response_class=HTMLResponse)
async def get_stats(request: Request):
    url = request.session.get('url', None)
    if not url:
        return 'Кажется вы забыли указать ссылку на статистику!'
    try:
        if await check_url(url):
            selected_levels = request.session.get('selected_levels', None)
            game_name, game_link = await get_game_name_link(url)
            all_levels, data = await parse_stats(url, selected_levels)
            return templates.TemplateResponse(
                'stats.html',
                {'request': request,
                 'game_name': game_name,
                 'game_link': game_link,
                 'all_levels': all_levels,
                 'selected_levels': selected_levels,
                 'data': data})
    except ClientConnectorError:
        return 'Ошибка подключения к серверу Encounter!'
    return 'Неверная ссылка на статистику!'


@app.post('/stats', response_class=HTMLResponse)
async def post_stats(request: Request,
                     selected_levels: Annotated[list, Form()]):
    request.session['selected_levels'] = selected_levels
    return RedirectResponse(url='/stats', status_code=303)
