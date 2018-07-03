SET @date_threshold = '2018-06-11 00:00:00';

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

#DROP TEMPORARY TABLE IF EXISTS first_line_emergence;
#CREATE TEMPORARY TABLE IF NOT EXISTS first_line_emergence AS
#(
#	SELECT ticket_id tid, create_time
#	FROM ticket_history
#	WHERE create_time > @date_threshold
#	AND queue_id = 5
#	GROUP BY ticket_id
#);

#DROP TEMPORARY TABLE IF EXISTS first_move_or_lock;
#CREATE TEMPORARY TABLE IF NOT EXISTS first_move_or_lock AS
#(
#	SELECT ticket_id tid, create_time
#	FROM ticket_history
#	WHERE create_time > @date_threshold
#	AND history_type_id in (16, 17)
#	GROUP BY ticket_id
#);

DROP TEMPORARY TABLE IF EXISTS first_line_first_response;
CREATE TEMPORARY TABLE IF NOT EXISTS first_line_first_response AS
(
	SELECT first_line_emergence.tid tid,
			 TIMESTAMPDIFF(SECOND, first_line_emergence.create_time, first_move_or_lock.create_time) as diff,
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
		SELECT min(id) as id, ticket_id tid, create_time
		FROM ticket_history
		WHERE create_time > @date_threshold
		AND history_type_id in (16, 17)
		GROUP BY ticket_id
	) first_move_or_lock
	ON first_line_emergence.tid = first_move_or_lock.tid
	WHERE first_line_emergence.id < first_move_or_lock.id
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
       first_move_or_lock_time
FROM main_ticket_info mti
LEFT JOIN client_request_info cri ON mti.tid = cri.tid
LEFT JOIN pending_auto_close pac ON mti.tid = pac.tid
LEFT JOIN closed_successful cs ON mti.tid = cs.tid
LEFT JOIN moved ON mti.tid = moved.tid
LEFT JOIN first_line_first_response flfr ON mti.tid = flfr.tid

#LEFT JOIN first_line_emergence fle ON mti.tid = fle.tid
#LEFT JOIN first_move_or_lock fmol ON mti.tid = fmol.tid