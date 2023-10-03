import re
import datetime as dt


def convert_seconds(value):
    if isinstance(value, tuple):
        value = list(value)
        value[1] = str(dt.timedelta(seconds=value[1]))
    return value


def get_seconds(lst):
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


def parse_bonus_penalty(str_time, value):
    bp_time = ''.join(str_time.partition(value)[2].split())
    bp_time = re.findall(r'\d{1,2}\w', bp_time)
    return get_seconds(bp_time)


def parse_value_teams(value: str) -> list[str, dt.datetime]:
    if isinstance(value, str):
        str_time = re.sub(r'таймаут', '', value)
        team_name = str_time.partition(' (')[0]
        level_date = re.search(r'\d\d\.\d\d\.\d\d\d\d', value)
        level_time = re.search(r'\d\d:\d\d:\d\d\.\d\d\d', value)
        level_datetime = dt.datetime.strptime(
            (level_date[0] + ' ' + level_time[0]),
            '%d.%m.%Y %H:%M:%S.%f')

        # bonus = re.search(r'\bбонус\b', value)
        # if bonus:
        #     bonus_seconds = parse_bonus_penalty(str_time, 'бонус')
        #     level_datetime -= dt.timedelta(seconds=bonus_seconds)
        #
        # penalty = re.search(r'\bштраф\b', value)
        # if penalty:
        #     penalty_seconds = parse_bonus_penalty(str_time, 'штраф')
        #     level_datetime += dt.timedelta(seconds=penalty_seconds)
    else:
        team_name, level_datetime = 0, 0
    return [team_name, level_datetime]
