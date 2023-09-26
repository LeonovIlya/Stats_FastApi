import io
import re
import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from pprint import pprint
import time

from app.parser.time_parser import parse_value

url = "https://dozorekb.en.cx/GameStat.aspx?gid=76109"
HEADERS = {'User-Agent': 'Mozilla/5.0'}


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            return await resp.text()


async def get_levels(url):
    response = await get_html(url)
    soup = BeautifulSoup(response, 'html.parser')
    levels = [i.get_text() for i in soup.find(
        name='tr',
        attrs={'class': 'levelsRow'})]
    return levels[2:-4]


async def get_commands(url):
    response = await get_html(url)
    soup = BeautifulSoup(response, 'html.parser')
    commands = set()
    commands_divs = soup.find_all(
        name='div',
        attrs={'class': 'dataCell'})
    for div in commands_divs:
        commands.add(div.find('a').get_text())
    return commands


async def get_commands_stats():
    response = await get_html(url)
    soup = BeautifulSoup(response, 'html.parser')
    table = soup.find('table', {'id': 'GameStatObject_DataTable'})
    df = pd.read_html(str(table))[0]
    df = df.drop(df.index[25])
    df = df.drop(columns=[0, df.columns[-3], df.columns[-2], df.columns[-1]])
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index(drop=True)
    df.fillna(0)
    for i in df.columns.values:
        df[i] = df[i].apply(parse_value)
    return df.to_html(index=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start = 0
    try:
        start = time.time()
        coroutines = [loop.create_task(get_commands_stats())]
        loop.run_until_complete(asyncio.wait(coroutines))
    finally:
        loop.close()
        print(f"Время выполнения: {time.time() - start}")
