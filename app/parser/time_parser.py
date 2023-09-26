import re


def get_seconds(lst):
    seconds = 0
    for i in lst:
        if i.endswith('h'):
            seconds += (int(i.replace('h', '')) * 60 * 60)
        elif i.endswith('m'):
            seconds += (int(i.replace('m', '')) * 60)
        elif i.endswith('s'):
            seconds += int(i.replace('s', ''))
    return seconds


def parse_bonus_penalty(str_time, value):
    bp_time = ''.join(str_time.partition(value)[2].split())
    bp_time = re.findall(r'\d{1,2}\w', bp_time)
    return get_seconds(bp_time)


def parse_value(value):
    if isinstance(value, str):
        str_time = re.sub(r'timeout', '', value)
        name = str_time.partition(' (')[0]
        str_time_lst = re.sub(r'[(,)]',
                              '',
                              ''.join(re.findall(r'\([^()]*\)',
                                                 str_time)[1].split())).split('.')
        seconds = get_seconds(str_time_lst)

        bonus = re.search(r'\bbonus\b', value)
        if bonus:
            seconds -= parse_bonus_penalty(str_time, 'bonus')

        penalty = re.search(r'\bpenalty\b', value)
        if penalty:
            seconds += parse_bonus_penalty(str_time, 'penalty')
    else:
        name, seconds = 0, 0
    return [name, seconds]
