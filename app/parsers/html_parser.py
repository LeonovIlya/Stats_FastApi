import re
import datetime as dt
import time
import asyncio
import bs4
import numpy as np
import aiohttp
import pandas as pd
from url_parser import get_base_url
from bs4 import BeautifulSoup

from app.parsers.time_parser import parse_value_teams, convert_seconds

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


async def get_game_start_time(url: str):
    _, game_url = await get_game_name_link(url)
    response = await get_response(game_url + '&lang=ru')
    soup = BeautifulSoup(response, 'html.parser')
    start_time = soup.find('span',
                           string='Начало игры').find_next().text
    start_time = re.search(r'\d\d\.\d\d\.\d\d\d\d \d*:\d\d:\d\d',
                           start_time)
    start_time = dt.datetime.strptime(start_time[0], '%d.%m.%Y %H:%M:%S')
    return start_time


async def check_url(url: str) -> bool:
    return bool(re.search('en.cx/GameStat.aspx\?gid=', url))


async def get_total_time(df: pd.DataFrame) -> list:
    total_times = {}
    for i in df.columns.values:
        for j in df[i]:
            print(j)
            k = j.split(',')
            if k[0] == '0':
                pass
            elif k[0] in total_times:
                total_times[j[0]] += int(k[1][:-3])
            else:
                total_times[j[0]] = int(k[1][:-3])
    return sorted(total_times.items(), key=lambda x: x[1])


async def get_table_from_url(url: str) -> bs4.element.Tag:
    response = await get_response(url + '&sortfield=SpentSeconds&lang=ru')
    soup = BeautifulSoup(response, 'html.parser')
    table = soup.find('table', {'id': ('GameStatObject_DataTable',
                                       'GameStatObject2_DataTable')})
    return table


async def table_to_dataframe(table: bs4.element.Tag) -> \
        pd.core.frame.DataFrame:
    df = pd.read_html(str(table), parse_dates=True)[0]  # читаем таблицу html
    df = df.drop(df.index[-1])  # удаляем нижнюю строку с дублированием
    # информации
    df = df.drop(columns=[0,
                          df.columns[-3],
                          df.columns[-2],
                          df.columns[-1]])  # удаляем лишние столбцы
    df.columns = df.iloc[0]  # заголовки столбцов = первая строка таблицы
    df = df[1:]  # удаляем лишнюю строку
    df = df.reset_index(drop=True)  # сбрасываем индекс без сохранения столбца
    df = df.fillna(0)  # заполняем нулями значения NaN
    return df


async def dataframe_to_html(
        df: pd.core.frame.DataFrame,
        lvl_list: list[str] = None) -> tuple[np.ndarray, str]:
    all_columns = df.columns.values  # получаем заголовки столбцов
    for i in all_columns:
        df[i] = df[i].apply(
            parse_value_teams)  # парсим каждую ячейку в столбцах

    # здесь нужна логика получения времени на уровне путем вычитания времен
    # уровней между собой, если уровень первый - вычитаем время уровня из
    # времени старта

    if lvl_list:
        df = df[lvl_list]  # выбираем нужные столбцы
    df['Общее время'] = pd.Series(await get_total_time(df))  # добавляем
    # новый столбец с общим временем выбранных столбцов для каждой команды
    df['Общее время'] = df['Общее время'].apply(convert_seconds)  #
    # конвертируем секунды в стандартный формат времени
    df.index = df.index + 1  # нумерация строк не с 0, а с 1
    return all_columns, df.to_html()


async def parse_stats(url: str, lvl_list: list[str] = None):
    table = await get_table_from_url(url)
    if table:
        dataframe = await table_to_dataframe(table)
        return await dataframe_to_html(dataframe, lvl_list)
    else:
        return 'Ошибка парсинга статистики! Проверьте доступность статистики ' \
               'или попробуйте еще раз!'


URL = 'https://dozorekb.en.cx/GameStat.aspx?gid=76109'
TEST_URL = 'test_stat.html'

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start = 0
    try:
        start = time.time()
        coroutines = [loop.create_task(get_game_start_time(URL))]
        loop.run_until_complete(asyncio.wait(coroutines))
    finally:
        loop.close()
        print(f"Время выполнения: {time.time() - start}")
