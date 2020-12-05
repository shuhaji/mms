from odoo import api, fields, models, tools


class BanquetReservationEventRoom(models.Model):
    """
    For Room Availability Views

    this model based on a view, not a table
    # https://odoo-development.readthedocs.io/en/latest/dev/py/postgres-views.html
    """
    _name = "banquet.reservation.event.room"
    _auto = False

    name = fields.Char(read_only=True)
    function_room_id = fields.Many2one('banquet.function.room', 'Function Room', read_only=True)
    room_name = fields.Char(read_only=True)
    join_to_room = fields.Char(read_only=True)
    reservation_event_id = fields.Many2one('banquet.reservation.event', 'Reservation Event', read_only=True)

    reservation_id = fields.Many2one('banquet.reservation', 'Reservation', read_only=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', read_only=True)
    partner_name = fields.Char(read_only=True)

    date_start = fields.Datetime(read_only=True)
    date_end = fields.Datetime(read_only=True)

    @api.model_cr
    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'event_question_report')
        self._cr.execute("""  drop view if exists banquet_reservation_event_room;
            CREATE OR REPLACE VIEW banquet_reservation_event_room AS (
                select (left(fr.id::varchar || '0000', 4) || s.id::varchar)::int as id, 
                fr."name" as room_name, 
                ' '::varchar as join_to_room, 
                fr.id as function_room_id,
                s.name as name, 
                s.id as reservation_event_id,
                s.reservation_id,
                s.company_id, 
                p.name as partner_name,
                s.date_start, 
                s.date_end
                from banquet_reservation_event s 
                left join banquet_reservation r on r.id = s.reservation_id
                left join res_partner p on p.id = r.partner_id
                left join banquet_function_room fr on fr.id = s.function_room_id	
                where s.date_start > 'now'::timestamp - '1 month'::interval	
                union 
                select (left(frc.id::varchar || '0000', 4) || s.id::varchar)::int as id, 
                frc."name" as room_name,
                '(' || fr."name" || ')' as join_to_room, 
                frc.id as function_room_id,
                s.name as name, 
                s.id as reservation_event_id,
                s.reservation_id,
                s.company_id, 
                p.name as partner_name,
                s.date_start, 
                s.date_end
                from banquet_reservation_event s 
                left join banquet_reservation r on r.id = s.reservation_id
                left join res_partner p on p.id = r.partner_id
                left join banquet_function_room fr on fr.id = s.function_room_id
                left join function_room_joined_rel j on j.function_room_id = fr.id
                left join banquet_function_room frc on frc.id = j.joined_id
                where s.date_start > 'now'::timestamp - '1 month'::interval
                and j.function_room_id is not null);
        """)
