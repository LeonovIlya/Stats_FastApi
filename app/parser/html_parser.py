import re
import asyncio
import time
import numpy as np
import aiohttp
import pandas as pd
from url_parser import get_base_url
from bs4 import BeautifulSoup
from typing import Union

from app.parser.time_parser import parse_value, convert_seconds

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) '
                  'Gecko/20100101 Firefox/28.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept-Language': 'en-US'
}


async def get_response(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            return await resp.text()


async def get_game_name_link(url: str) -> tuple[str, str]:
    response = await get_response(url)
    soup = BeautifulSoup(response, 'html.parser')
    game = soup.find(
        name='a',
        attrs={'id': 'lnkGameName'})
    game_url = get_base_url(url) + game['href']
    return game.get_text(), game_url


async def check_url(url: str) -> bool:
    return bool(re.search('en.cx/GameStat.aspx\?gid=', url))


async def get_total_time(df: pd.DataFrame) -> list:
    total_times = {}
    for i in df.columns.values:
        for j in df[i].tolist():
            if j[0] == 0:
                pass
            elif j[0] in total_times:
                total_times[j[0]] += int(j[1])
            else:
                total_times[j[0]] = int(j[1])
    return sorted(total_times.items(), key=lambda x: x[1])


async def get_commands_stats(url: str,
                             lvl_list: list = None) -> tuple[np.ndarray, str]:
    response = await get_response(url + '&sortfield=SpentSeconds')
    soup = BeautifulSoup(response, 'html.parser')
    table = soup.find('table', {'id': 'GameStatObject_DataTable'})
    df = pd.read_html(str(table))[0]
    df = df.drop(df.index[-1])
    df = df.drop(columns=[0, df.columns[-3], df.columns[-2], df.columns[-1]])
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index(drop=True)
    df.fillna(0)
    all_columns = df.columns.values
    for i in all_columns:
        df[i] = df[i].apply(parse_value)
    if lvl_list:
        df = df[lvl_list]
    df['Общее время'] = pd.Series(await get_total_time(df))
    df['Общее время'] = df['Общее время'].apply(convert_seconds)
    df.index = df.index + 1
    return all_columns, df.to_html()

URL = 'https://moscow.en.cx/GameStat.aspx?gid=73051&sortfield=SpentSeconds'

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start = 0
    try:
        start = time.time()
        coroutines = [loop.create_task(get_response(URL))]
        loop.run_until_complete(asyncio.wait(coroutines))
    finally:
        loop.close()
        print(f"Время выполнения: {time.time() - start}")
