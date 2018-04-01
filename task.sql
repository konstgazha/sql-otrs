SELECT *
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
						AND th.name LIKE '%%open%%pending auto close+%%'
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