# -*- coding: utf-8 -*-
"""
Created on Wed Aug  1 12:56:07 2018
@author: gazhakv
"""
import pandas as pd
from datetime import datetime
from dateutil import parser
import calendar


YEAR = 2018
LUNCH = range(43200, 45900)
WORKING_DATES = ['28.04.18', '09.06.18']
HOLIDAYS = ['29.04.18', '30.04.18', '01.05.18', '02.05.18', '09.05.18', '11.06.18', '12.06.18', '05.11.18']


def convert_to_seconds(hours, minutes):
    return hours * 3600 + minutes * 60


def compute_working_time(_start, _end, dayfirst=False, result_in_hours=True):
    end = parser.parse(_end, dayfirst=dayfirst)
    start = parser.parse(_start, dayfirst=dayfirst)
    result = 0
    for month in range(start.month, end.month + 1):
        days = end.day + 1
        first_day = start.day
        if month != end.month:
            days = calendar.monthrange(YEAR, month)[1] + 1
        if month != start.month:
            first_day = 1
        for day in range(first_day, days):
            next_date = str(day) + '.' + str(month) + '.' + str(YEAR)
            next_date = parser.parse(next_date, dayfirst=True).date()
            if ((next_date.weekday() < 5) or \
               (next_date in [parser.parse(i, dayfirst=True).date() for i in WORKING_DATES])) and \
               (next_date not in [parser.parse(i, dayfirst=True).date() for i in HOLIDAYS]):
                start_hour = 8
                start_minute = 30
                end_hour = 17
                end_minute = 30
                if next_date.weekday() == 4:
                    end_hour = 16
                    end_minute = 15
                if next_date == start.date():
                    if convert_to_seconds(start.hour, start.minute) >= \
                       convert_to_seconds(start_hour, start_minute):
                        start_hour = start.hour
                        start_minute = start.minute
                    if convert_to_seconds(start.hour, start.minute) >= \
                       convert_to_seconds(end_hour, end_minute):
                           start_hour = end_hour
                           start_minute = end_minute
                        
                if next_date == end.date():
                    if convert_to_seconds(end.hour, end.minute) <= \
                       convert_to_seconds(end_hour, end_minute):
                        end_hour = end.hour
                        end_minute = end.minute
                    if convert_to_seconds(end_hour, end_minute) <= \
                       convert_to_seconds(start_hour, start_minute):
                           start_hour = end_hour
                           start_minute = end_minute
                
                converted_start = convert_to_seconds(start_hour, start_minute)
                converted_end = convert_to_seconds(end_hour, end_minute)
                lunch_difference = set(range(converted_start, 
                                             converted_end)).difference(set(LUNCH))
                lunch_difference = list(lunch_difference)
                if lunch_difference:
                    converted_start = lunch_difference[0]
                    converted_end = converted_start + len(lunch_difference)
                    result += converted_end - converted_start
                else:
                    result += 0
    if result_in_hours:
        result /= 3600
    return result


def line_working_time(df, queue_name, name_emergence_time, name_lock_time):
    emergence_time = df[name_emergence_time]
    lock_time = df[name_lock_time]
    in_working = []
    for i in range(len(df)):
        try:
            result = compute_working_time(emergence_time[i], lock_time[i], False)
            in_working.append(result)
        except Exception as e:
            in_working.append('')
    result_column = 'in_working_' + queue_name
    df[result_column] = in_working


def make_report(df):
    time_create = df['tcreatetime']
    autoclose = df['auto_close']
    time_close = df['closed']
    auto_close = []
    forced_close = []
    for i in range(len(df)):
        try:
            result = compute_working_time(time_create[i], autoclose[i], False)
            auto_close.append(result)
        except Exception as e:
            auto_close.append('')
        try:
            result = compute_working_time(time_create[i], time_close[i], False)
            forced_close.append(result)
        except Exception as e:
            forced_close.append('')
    df['auto_closed'] = auto_close
    df['forced_close'] = forced_close


def compute():
    df = pd.read_csv('report.csv', sep=';', encoding='ansi')
    make_report(df)
    line_working_time(df, 'first', 'first_line_emergence_time', 'first_move_or_lock_time')
    line_working_time(df, 'others', 'others_line_emergence_time', 'others_line_lock_time')
    df.to_csv('report_computed.csv', sep=';')


if __name__ == '__main__':
    compute()
