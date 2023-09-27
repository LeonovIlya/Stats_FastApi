import asyncio
import time
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup


from app.parser.time_parser import parse_value, convert_seconds

URL = "https://dozorekb.en.cx/GameStat.aspx?gid=76109"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

lst_clmns = ['89: Поиск х1', '90: Поиск х2', '91: Поиск х3',
             '92: Поиск х4', '93: Поиск х5', '94: Поиск х6', '95: Поиск х7']


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            return await resp.text()


async def get_levels():
    response = await get_html(URL)
    soup = BeautifulSoup(response, 'html.parser')
    levels = [i.get_text() for i in soup.find(
        name='tr',
        attrs={'class': 'levelsRow'})]
    return levels[2:-4]


async def get_commands():
    response = await get_html(URL)
    soup = BeautifulSoup(response, 'html.parser')
    commands = set()
    commands_divs = soup.find_all(
        name='div',
        attrs={'class': 'dataCell'})
    for div in commands_divs:
        commands.add(div.find('a').get_text())
    return commands


async def get_total_time(df):
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


async def get_commands_stats():
    response = await get_html(URL)
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
    df = df[lst_clmns]
    print(df.index)
    df['Общее время'] = pd.Series(await get_total_time(df))
    df['Общее время'] = df['Общее время'].apply(convert_seconds)
    print(df.index)
    df.index = df.index + 1
    return df.to_html()


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
