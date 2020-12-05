from odoo import models, api, fields


class ReportPosOutlet(models.AbstractModel):
    _name = 'report.kg_pos.report_pos_outlet'

    @api.model
    def get_report_values(self, docids,  data=None):

        working_date = data['working_date']
        company_id = data['company_id']
        company_name = data['company_name']
        shift_id = data['shift_id']
        if shift_id:
            where_shift = "AND a.shift_id = '" + str(shift_id) + "' "
            shift_desc = data['shift_desc']
        else:
            where_shift = ""
            shift_desc = "ALL"

        query = """
            with z_pos_order_summary_by_outlet as (
                select b.id, i."name" as outlet, b."name" as order_ref, g.meal_type as item, b.customer_count as guest,
                    sum(c.price_subtotal_incl) as  total, 
                    sum(case when h.name = 'Food' then c.price_subtotal else 0 end) as food,
                    sum(case when h.name = 'Food' then c.qty else 0 end) as food_cover,
                    sum(case when h.name = 'Beverage' then c.price_subtotal else 0 end) as beverage,
                    sum(case when h.name = 'Beverage' then c.qty else 0 end) as beverage_cover,
                    sum(case when h.name = 'Other' then c.price_subtotal else 0 end) as other,
                    sum(c.service_amount) as service, sum(c.tax_amount) as tax,
                    case when b.is_hotel_guest = 'true' then 'IN' else 'OUT' end as guest_type
                from pos_session a left join pos_order b on a.id = b.session_id
                    left join pos_order_line c on b.id = c.order_id
                    left join product_product e on c.product_id = e.id
                    left join product_template f on e.product_tmpl_id = f.id
                    left join meal_time_line g on b.meal_time_line_id = g.id
                    left join product_category h on f.categ_id = h.id
                    left join pos_category i on b.outlet_id = i.id
                where a.working_date = %s
                    and b.company_id = %s                    
                    """ + where_shift + """ 
                    and b.state in ('paid', 'invoiced', 'done')            
                    and h.name in ('Food', 'Beverage', 'Other')
                group by i."name", b."name", g.meal_type,  b.id, b.customer_count
                ),
                z_pax_summary as (
                    select id, outlet, order_ref, item, SUM(guest) as guest, SUM(total) as total 
                        ,SUM(food) as food, SUM(food_cover) as food_cover, SUM(beverage) as beverage
                        ,SUM(beverage_cover) as beverage_cover, SUM(other) as other
                        ,SUM(service) as service, SUM(tax) as tax
                        ,SUM(case when guest_type = 'IN' then guest else 0 end) as cover_in
                        ,SUM(case when guest_type = 'OUT' then guest else 0 end) as cover_out
                    from z_pos_order_summary_by_outlet
                    group by id, outlet, order_ref, item
                ),
                z_pos_order_payment_journal as (
                select b.id, array_to_string(array_agg(distinct j."name"), ',') as payment_journal 
                from pos_session a left join pos_order b on a.id = b.session_id
                    left join account_bank_statement_line d on b.id = d.pos_statement_id
                    left join account_journal j on d.journal_id = j.id
                where a.working_date = %s
                    and b.company_id = %s                    
                    """ + where_shift + """ 
                    and b.state in ('paid', 'invoiced', 'done')
                group by b.id)
                         
            select outlet, order_ref, item, total, food, beverage, other, service, tax, guest, cover_in, cover_out
                , payment_journal
                , food_cover
                , beverage_cover
            from z_pax_summary o
            left join z_pos_order_payment_journal p on o.id = p.id
            order by outlet, order_ref
            """

        self.env.cr.execute(query, (working_date, company_id, working_date, company_id))

        outlet = self.env.cr.dictfetchall()

        query_payment = """
            select jpg.name, jpg.pms_payment_type, sum(coalesce(absl.amount, 0)) as amount,
            case when jpg.pms_payment_type = 'H' then count(amount) else 0 end as chg_room
            from journal_payment_group jpg
            left join account_journal ac on ac.company_id = %s
                and jpg.id = ac.journal_payment_group_id
            left join pos_config c on c.company_id = ac.company_id
            left join pos_session a on c.id = a.config_id
                and a.working_date = %s                   
                """ + where_shift + """ 
            left join account_bank_statement abs on abs.pos_session_id = a.id
            left join account_bank_statement_line absl on absl.statement_id = abs.id
                and ac.id = absl.journal_id
            where jpg.active is true
            group by jpg.name, jpg.pms_payment_type
            order by jpg.name
            """

        self.env.cr.execute(query_payment, (company_id, working_date))

        payments = self.env.cr.dictfetchall()

        return {
            'outlet': outlet,
            'payments': payments,
            'working_date': working_date,
            'company_name': company_name,
            'shift_desc': shift_desc,
            'printed_by': self.env.user.name,
            'printed_on': fields.Date.context_today(self),
        }

