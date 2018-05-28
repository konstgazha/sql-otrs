SET @date_threshold = '2018-04-01 00:00:00';

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
	WHERE
		t.create_time > @date_threshold
);

# Client request info
SELECT * FROM main_ticket_info
LEFT JOIN
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
) s ON main_ticket_info.tid = s.tid;