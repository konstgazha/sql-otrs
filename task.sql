SELECT thid, tcreatetime, thpendingautoclose, thclose, artbody, sername, name, diff
FROM
(
	SELECT thid, tcreatetime, thpendingautoclose, thclose, artbody, sername, name
	FROM
	(
		SELECT thid, userid, tcreatetime, thpendingautoclose, thclose, artbody, sername
		FROM
		(
			SELECT thid, userid, tcreatetime, tserviceid, thpendingautoclose, thclose, artbody
			FROM
			(
				SELECT thid, userid, tcreatetime, tserviceid, thpendingautoclose, thclose
				FROM
				(
					SELECT thid, userid, tcreatetime, tserviceid, thpendingautoclose
					FROM
					(
						SELECT thid, userid, tcreatetime, tserviceid
						FROM
						    (
						        # Ticket History
						        SELECT DISTINCT
						            MIN(th.ticket_id) thid
						        FROM ticket_history th
						        WHERE
						            th.create_time > '2018-01-01 00:00:00'
						        GROUP BY th.ticket_id
						    ) s1
						RIGHT JOIN
						    (
						        # Ticket
						        SELECT
						            t.id tid,
						            t.create_time tcreatetime,
						            t.service_id tserviceid,
						            t.user_id userid
						        FROM ticket t
						        WHERE
						            t.create_time > '2018-01-01 00:00:00'
						    ) s2
						ON s2.tid = s1.thid
					) s3
					LEFT JOIN
					(
						SELECT
							th.ticket_id tid,
							MAX(th.create_time) thpendingautoclose
						FROM ticket_history th
						WHERE
							th.create_time > '2018-01-01 00:00:00'
							AND th.name IN ('%%open%%pending auto close+%%', '%%pending auto close+%%open%%')
						GROUP BY tid
					) s4
					ON s3.thid = s4.tid
				) s5
				LEFT JOIN
				(
					SELECT
						th.ticket_id tid,
						MAX(th.create_time) thclose
					FROM ticket_history th
					WHERE
						th.create_time > '2018-01-01 00:00:00'
						AND th.name IN ('%%pending auto close+%%closed successful%%', '%%Close')
					GROUP BY tid
				) s6
				ON s5.thid = s6.tid
			) s7
			LEFT JOIN
			(
				SELECT
					art.ticket_id tid,
					MIN(art.a_body) artbody
				FROM article art
				WHERE
					art.create_time > '2018-01-01 00:00:00'
					AND art.article_sender_type_id = '3'
				GROUP BY tid
			) s8
			ON s7.thid = s8.tid
		) s9
		LEFT JOIN
		(
			SELECT
				ser.id serid,
				ser.name sername
			FROM service ser
		) s10
		ON s9.tserviceid = s10.serid
	) s11
	LEFT JOIN
	(
		SELECT
			usr.id userid,
			concat(usr.last_name, " ", usr.first_name) name
		FROM users usr
	) s12
	ON s11.userid = s12.userid
) s13
LEFT JOIN
(
	SELECT tid, name_start, name_move, diff
	FROM
	(
		SELECT s14.tid AS tid, name_start, name_move, TIMESTAMPDIFF(SECOND, create_time2, create_time1) AS diff
		FROM
		(
			SELECT DISTINCT ticket_id tid, name name_move, MIN(th.create_time) create_time1
			FROM ticket_history th
			WHERE th.history_type_id IN (16, 17)
			AND th.create_time > '2018-01-01 00:00:00'
			GROUP BY th.ticket_id
		) s15
		RIGHT JOIN
		(
			SELECT DISTINCT ticket_id tid, name name_start, MIN(th.create_time) create_time2
			FROM ticket_history th
			WHERE th.history_type_id = 4
			AND th.create_time > '2018-01-01 00:00:00'
			GROUP BY th.ticket_id
		) s14
		ON s15.tid = s14.tid
	) s17
	RIGHT JOIN
	(
		SELECT DISTINCT MIN(ticket_id) tid2
		FROM ticket_history th
		WHERE (th.name LIKE '%Первая линия%' OR th.name LIKE '%ОГБУ ЧРЦНИТ%')
		AND th.create_time > '2018-01-01 00:00:00'
		GROUP BY th.ticket_id 
	) s18
	ON s17.tid = s18.tid2
) s16
ON s13.thid = s16.tid