# -*- coding: utf-8 -*-
"""
Created on Tue Dec 11 13:33:56 2018

@author: gazhakv
"""
import MySQLdb
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser
import seaborn


db = MySQLdb.connect("10.0.1.195",
                     "",
                     "",
                     "",
                     charset='utf8',
                     init_command='SET NAMES UTF8')


sql_request = """
SET @date_threshold = '{0} 00:00:00';
DROP TEMPORARY TABLE IF EXISTS main_ticket_info;
CREATE TEMPORARY TABLE IF NOT EXISTS main_ticket_info AS
(
    SELECT DISTINCT
            t.tn tn,
            t.id tid,
            t.create_time tcreatetime,
            ser.name service_name,
            concat(usr.last_name, " ", usr.first_name) user_name,
            ts.name ticket_state_name,
            q.name queue_name
    FROM ticket t
    LEFT JOIN service ser ON t.service_id = ser.id
    LEFT JOIN users usr ON t.user_id = usr.id
    LEFT JOIN ticket_state ts ON t.ticket_state_id = ts.id
    LEFT JOIN queue q ON t.queue_id = q.id
    WHERE t.create_time > @date_threshold
);

# Client request info
DROP TEMPORARY TABLE IF EXISTS client_request_info;
CREATE TEMPORARY TABLE IF NOT EXISTS client_request_info AS
(
    SELECT main_art_info.tid tid, artbody, artsubject, note FROM
    (
        SELECT
            MIN(art.ticket_id) tid,
            art.a_body artbody,
            art.a_subject artsubject
        FROM article art
        WHERE
            art.create_time > @date_threshold
            AND art.article_sender_type_id = '3'
        GROUP BY art.ticket_id
    ) main_art_info
    LEFT JOIN
    (
        SELECT
            MIN(art.ticket_id) tid,
            art.a_body note
        FROM article art
        WHERE
            art.create_time > @date_threshold
            AND art.a_subject = 'Заметка'
        GROUP BY art.ticket_id
    ) note_info
    ON main_art_info.tid = note_info.tid
);

DROP TEMPORARY TABLE IF EXISTS pending_auto_close;
CREATE TEMPORARY TABLE IF NOT EXISTS pending_auto_close AS
(
    SELECT tid, create_time auto_close
    FROM ticket_history th
    INNER JOIN (SELECT MAX(id) id, ticket_id tid
                    FROM ticket_history th
                    WHERE
                        th.create_time > @date_threshold
                        AND th.state_id IN (7, 8)
                    GROUP BY tid) thids
    ON th.id = thids.id
    WHERE th.create_time > @date_threshold
);

DROP TEMPORARY TABLE IF EXISTS closed_successful;
CREATE TEMPORARY TABLE IF NOT EXISTS closed_successful AS
(
    SELECT tid, create_time closed
    FROM ticket_history th
    INNER JOIN (SELECT MAX(id) id, ticket_id tid
                    FROM ticket_history th
                    WHERE
                        th.create_time > @date_threshold
                        AND th.state_id = 2
                    GROUP BY tid) thids
    ON th.id = thids.id
    WHERE th.create_time > @date_threshold
);

DROP TEMPORARY TABLE IF EXISTS moved;
CREATE TEMPORARY TABLE IF NOT EXISTS moved AS
(
    SELECT COUNT(*) moved_count, th.ticket_id tid
    FROM ticket_history th
    WHERE create_time > @date_threshold
    AND history_type_id = 16
    GROUP BY th.ticket_id
);

# Counting time of response for the first line
DROP TEMPORARY TABLE IF EXISTS first_line_first_response;
CREATE TEMPORARY TABLE IF NOT EXISTS first_line_first_response AS
(
    SELECT first_line_emergence.tid tid,
             min(TIMESTAMPDIFF(SECOND, first_line_emergence.create_time, first_move_or_lock.create_time)) as diff,
             first_line_emergence.create_time as first_line_emergence_time,
             first_move_or_lock.create_time as first_move_or_lock_time
    FROM
    (
        SELECT min(id) as id, ticket_id tid, create_time
        FROM ticket_history
        WHERE create_time > @date_threshold
        AND queue_id = 5
        GROUP BY ticket_id
    ) first_line_emergence
    LEFT JOIN
    (
        SELECT id, ticket_id tid, create_time
        FROM ticket_history
        WHERE create_time > @date_threshold
        AND history_type_id in (16, 17)
    ) first_move_or_lock
    ON first_line_emergence.tid = first_move_or_lock.tid
    WHERE first_line_emergence.id < first_move_or_lock.id
    GROUP BY tid
);

# Counting time of response for others
DROP TEMPORARY TABLE IF EXISTS others_line_first_response;
CREATE TEMPORARY TABLE IF NOT EXISTS others_line_first_response AS
(
    SELECT others_line_emergence.tid tid,
             min(TIMESTAMPDIFF(SECOND, others_line_emergence.create_time, others_line_lock.create_time)) as diff_others,
             others_line_emergence.create_time as others_line_emergence_time,
             others_line_lock.create_time as others_line_lock_time
    FROM
    (
        SELECT min(id) as id, ticket_id tid, create_time, queue_id as queue_id_nominated
        FROM ticket_history
        WHERE create_time > @date_threshold
        AND history_type_id = 16
        AND create_by <> 1
        GROUP BY ticket_id
    ) others_line_emergence
    LEFT JOIN
    (
        SELECT id, ticket_id tid, create_time, queue_id as queue_id_performer
        FROM ticket_history
        WHERE create_time > @date_threshold
        AND history_type_id in (16, 17, 18)
    ) others_line_lock
    ON others_line_emergence.tid = others_line_lock.tid
    WHERE others_line_emergence.id < others_line_lock.id
    AND queue_id_performer = queue_id_nominated
    GROUP BY tid
);

SELECT tn,
       mti.tid,
       tcreatetime,
       service_name,
       user_name,
       ticket_state_name,
       queue_name,
       artbody,
       artsubject,
       note,
       auto_close,
       closed,
       moved_count,
       diff,
       first_line_emergence_time,
       first_move_or_lock_time,
       diff_others,
       others_line_emergence_time,
       others_line_lock_time
FROM main_ticket_info mti
LEFT JOIN client_request_info cri ON mti.tid = cri.tid
LEFT JOIN pending_auto_close pac ON mti.tid = pac.tid
LEFT JOIN closed_successful cs ON mti.tid = cs.tid
LEFT JOIN moved ON mti.tid = moved.tid
LEFT JOIN first_line_first_response flfr ON mti.tid = flfr.tid
LEFT JOIN others_line_first_response olfr ON mti.tid = olfr.tid
"""


date = '2018-12-01'
c = db.cursor(MySQLdb.cursors.DictCursor)

[c.execute(sql) for sql in sql_request.format(date).split(';')]

data = c.fetchall()
# ticket_id = list(map(lambda x: list(x.values())[0], data))
data[0]['tcreatetime'].time() > parser.parse('8:30').time()


users = list(set([d['user_name'] for d in data]))
#df = pd.DataFrame([0]*len(users), users, [parser.parse(date).strftime('%d.%m.%Y')])
queues = list(set([d['service_name'] for d in data]))
df = pd.DataFrame([0]*len(queues), queues, [parser.parse(date).strftime('%d.%m.%Y')])


first_line_users = ['Чурянина Ольга', 'Портнова Дарья Сергеевна',
                    'службы поддержки Администратор', 'Баландина Анастасия Павловна',
                    'Хатылова Лилия', 'Курманова Диляра Жаудатовна',
                    'Никитина Ольга', 'Деняева Светлана Юрьевна',
                    'Уварова Марина']

def count_first_line():
    # FIRST LINE! FIIIIRST LIIINE!!!!! THIRST LINE
    for k in data:
        if k['user_name'] in first_line_users:
            current_date = k['tcreatetime']
            if k['first_move_or_lock_time']:
                end_date = k['first_move_or_lock_time'].date()
            elif k['auto_close']:
                end_date = k['auto_close'].date()
            else:
                end_date = datetime.now().date()
            while current_date.date() <= end_date:
                if current_date.strftime('%d.%m.%Y') not in df.columns:
                    df[current_date.strftime('%d.%m.%Y')] = 0
                df.at[k['user_name'], current_date.strftime('%d.%m.%Y')] += 1
                current_date += timedelta(days=1)

def count_others():
    # OTHERS! OOTHERRRS!!!
    for k in data:
        if k['user_name'] not in first_line_users:
            if k['others_line_emergence_time']:
                current_date = k['others_line_emergence_time']
            else:
                current_date = k['tcreatetime']
            if 'close' in k['ticket_state_name'] and k['closed']:
                end_date = k['closed'].date()
            else:
                end_date = datetime.now().date()
            while current_date.date() <= end_date:
                if current_date.strftime('%d.%m.%Y') not in df.columns:
                    df[current_date.strftime('%d.%m.%Y')] = 0
                df.at[k['user_name'], current_date.strftime('%d.%m.%Y')] += 1
                #if current_date.strftime('%d.%m.%Y') == '11.12.2018' and k['user_name'] == 'Гажа Константин Владимирович':
                #    print(k['tn'])
                current_date += timedelta(days=1)

def count_similar_queue():
    for k in data:
        if k['others_line_emergence_time']:
            current_date = k['others_line_emergence_time']
        else:
            current_date = k['tcreatetime']
        if 'close' in k['ticket_state_name']:
            if k['auto_close']:
                if k['auto_close'].time() < parser.parse('8:30').time():
                    end_date = k['auto_close'].date() - timedelta(days=1)
                else:
                    end_date = k['auto_close'].date()
            elif k['closed']:
                if k['closed'].time() < parser.parse('8:30').time():
                    end_date = k['closed'].date() - timedelta(days=1)
                else:
                    end_date = k['closed'].date()
        else:
            end_date = datetime.now().date()
        while current_date.date() <= end_date:
            if current_date.strftime('%d.%m.%Y') not in df.columns:
                df[current_date.strftime('%d.%m.%Y')] = 0
            df.at[k['service_name'], current_date.strftime('%d.%m.%Y')] += 1
            #if current_date.strftime('%d.%m.%Y') == '11.12.2018' and k['user_name'] == 'Гажа Константин Владимирович':
            #    print(k['tn'])
            current_date += timedelta(days=1)

#count_first_line()
#count_others()
count_similar_queue()

df.to_csv('count_request.csv', encoding='ansi')