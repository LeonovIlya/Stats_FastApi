import re
import datetime as dt
import time
import asyncio
import bs4
import numpy as np
import aiohttp
import pandas as pd
import swifter
from url_parser import get_base_url
from bs4 import BeautifulSoup

from app.parsers.time_parser import get_total_time, parse_value_teams

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:28.0) '
                  'Gecko/20100101 Firefox/28.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest'
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


async def get_game_start_time(url: str) -> dt.datetime:
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


def repr_value(value: list) -> str:
    if len(value) == 2:
        return f'{value[0]}<br>{value[1]}'
    elif len(value) == 3:
        if value[2] == 0:
            return f'{value[0]}<br>{value[1]}'
        elif value[2] > 0:
            return f'{value[0]}<br>{value[1]}<br>Штраф: {value[2]} c.'
        elif value[2] < 0:
            return f'{value[0]}<br>{value[1]}<br>Бонус: {abs(value[2])} c.'


async def dataframe_to_html(
        df: pd.core.frame.DataFrame,
        game_start: dt.datetime,
        lvl_list: list[str] = None) -> tuple[np.ndarray, str]:

    all_columns = df.columns.values  # получаем все заголовки столбцов
    for i in all_columns:
        df[i] = df[i].swifter.apply(parse_value_teams)  # парсим каждую ячейку
        # в столбцах и получаем лист [команда, время апа]

    for index, column in reversed(list(enumerate(df))):
        if index != 0:
            current_column = df[column]
            previous_column = df.iloc[:, index - 1]
            for i in current_column.values:
                name = i[0]
                current_datetime = i[1]
                previous_datetime = 0
                for j in previous_column:
                    if j[0] == name:
                        previous_datetime = j[1]
                if current_datetime != 0:
                    i[1] = current_datetime - previous_datetime
        elif index == 0:
            for i in df[column].values:
                i[1] -= game_start

    if lvl_list:
        df = df[lvl_list]  # выбираем нужные столбцы

    clear_time, total_time = await get_total_time(df)
    df.loc[:, 'Общее чистое время'] = pd.Series(clear_time)
    df.loc[:, 'Общее время с учетом бонусов и штрафов'] = pd.Series(total_time)
    df = df.swifter.applymap(repr_value)
    df.index = df.index + 1  # нумерация строк с 1
    df['Место'] = df.index
    return all_columns, df.to_html(index_names=False, escape=False)


async def parse_stats(url: str, lvl_list: list[str] = None):
    table = await get_table_from_url(url)
    if table:
        dataframe = await table_to_dataframe(table)
        game_start = await get_game_start_time(url)
        return await dataframe_to_html(dataframe, game_start, lvl_list)
    else:
        return 'Ошибка парсинга статистики! Проверьте доступность статистики '\
               'или попробуйте еще раз!'
