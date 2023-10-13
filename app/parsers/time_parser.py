import re
import datetime as dt
import pandas as pd


def get_seconds(lst: list) -> int:
    seconds = 0
    for i in lst:
        if i.endswith('М'):
            seconds += (int(i.replace('М', '')) * 24 * 60 * 60)
        elif i.endswith('д'):
            seconds += (int(i.replace('д', '')) * 24 * 60 * 60)
        elif i.endswith('ч'):
            seconds += (int(i.replace('ч', '')) * 60 * 60)
        elif i.endswith('м'):
            seconds += (int(i.replace('м', '')) * 60)
        elif i.endswith('с'):
            seconds += int(i.replace('с', ''))
    return seconds


def parse_bonus_penalty(str_time: str, value: str) -> int:
    bp_time = ''.join(str_time.partition(value)[2].split())
    bp_time = re.findall(r'\d{1,2}\w', bp_time)
    return get_seconds(bp_time)


def parse_value_teams(value: str) -> list[str, dt.datetime]:
    correction = 0
    if isinstance(value, str):
        str_time = re.sub(r'таймаут', '', value)
        team_name = str_time.partition(' (')[0]
        level_date = re.search(r'\d\d\.\d\d\.\d\d\d\d', value)
        level_time = re.search(r'\d\d:\d\d:\d\d\.\d\d\d', value)
        level_datetime = dt.datetime.strptime(
            (level_date[0] + ' ' + level_time[0]),
            '%d.%m.%Y %H:%M:%S.%f')

        bonus = re.search(r'\bбонус\b', value)
        if bonus:
            bonus_seconds = parse_bonus_penalty(str_time, 'бонус')
            correction -= bonus_seconds
        penalty = re.search(r'\bштраф\b', value)
        if penalty:
            penalty_seconds = parse_bonus_penalty(str_time, 'штраф')
            correction += penalty_seconds
    else:
        team_name, level_datetime = None, 0
    return [team_name, level_datetime, correction]


async def get_total_time(df: pd.DataFrame) -> tuple[list, list]:
    clear_total_times = {}
    total_times = {}
    lvl_counter = 1
    for i in df.columns.values:
        for j in df[i]:
            if j[0] is None:
                pass
            elif j[0] in clear_total_times:
                clear_total_times[j[0]][0] += j[1]
                clear_total_times[j[0]][1] += 1
                total_times[j[0]][0] += (j[1] + dt.timedelta(seconds=j[2]))
                total_times[j[0]][1] += 1
            else:
                clear_total_times[j[0]] = [j[1], lvl_counter]
                total_times[j[0]] = [(j[1] + dt.timedelta(seconds=j[2])),
                                     lvl_counter]
    return sorted(clear_total_times.items(),
                  key=lambda x: (-x[1][1], x[1][0])), \
           sorted(total_times.items(),
                  key=lambda x: (-x[1][1], x[1][0]))
