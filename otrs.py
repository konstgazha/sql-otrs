# -*- coding: utf-8 -*-
import MySQLdb
import pandas as pd
from working_time import compute_working_time
import math


db = MySQLdb.connect("10.0.1.195",
                     "",
                     "",
                     "",
                     charset='utf8',
                     init_command='SET NAMES UTF8')


sql_request = """
SET @date_threshold = '{0} 00:00:00';
SELECT DISTINCT t.id FROM ticket t
LEFT JOIN ticket_history th ON t.id = th.ticket_id
WHERE t.create_time > @date_threshold
AND th.state_id = 11
"""


date = '2018-10-01'
c = db.cursor(MySQLdb.cursors.DictCursor)

[c.execute(sql) for sql in sql_request.format(date).split(';')]

data = c.fetchall()
ticket_id = list(map(lambda x: list(x.values())[0], data))


ticket_info = """
select id, state_id, ticket_id, create_time, history_type_id, create_by from ticket_history
where ticket_id in {0}
"""

c.execute(ticket_info.format(str(tuple(ticket_id))))
data = c.fetchall()
ticket_history = list(map(lambda x: list(x.values()), data))

ticket_info = {x: [] for x in ticket_id}
df = pd.DataFrame(ticket_history)


def compute_contractor_time(task):
    time = 0
    _start = None
    _end = None
    for idx, val in task.iterrows():
        if idx != 0 and val[1] == 11:
            if task.loc[idx-1][1] != 11:
                _start = val[3]
            if idx + 1 in task.index:
                if task.loc[idx+1][1] != 11:
                    _end = task.loc[idx+1][3]
            else:
                _end = val[3]
        if _start and _end:
            diff = compute_working_time(_start.strftime("%Y-%m-%d %H:%M"), _end.strftime("%Y-%m-%d %H:%M"))
            time += diff
            _start = None
            _end = None
    return time

for k in ticket_info.keys():
    ticket_info[k] = compute_contractor_time(df[df[2] == k])

result = pd.read_csv('report_computed.csv', sep=';')

for idx, val in result.iterrows():
    if val.tid in ticket_info.keys():
        if not math.isnan(val['forced_close']):
            if val['forced_close'] > ticket_info[val.tid]:
                #result.set_value(idx, 'forced_close', val['forced_close'] - ticket_info[val.tid])
                result.at[idx, 'forced_close'] = val['forced_close'] - ticket_info[val.tid]
        if not math.isnan(val['auto_closed']):
            if val['auto_closed'] > val['forced_close']:
                #print('kek')
                #result.set_value(idx, 'auto_closed', val['auto_closed'] - ticket_info[val.tid])
                result.at[idx, 'auto_closed'] = val['auto_closed'] - ticket_info[val.tid]
result.to_csv('report_final_result2.csv', sep=';', encoding='ansi', decimal=',')
