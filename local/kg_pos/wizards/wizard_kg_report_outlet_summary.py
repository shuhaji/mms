from odoo import api, fields, models, _


class WizardOutletSummary(models.TransientModel):
    _inherit = 'wizard.kg.report.base'
    _name = 'wizard.kg.report.outlet.summary'
    _title = "KG Report - Outlet Summary"

    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id.id)
    working_date = fields.Date(required=True, default=fields.Date.today)

    @api.multi
    def _get_data(self):
        """ get data from database or any other source

        :return: dict or list of dict
        """
        # return {
        #     "test": "abc", "test2": 123
        # }
        # return [
        #     {"test": "abc", "test2": 123},
        #     {"test": "cde", "test2": 124}
        # ]
        # multi key data:
        # return {
        #     "companyInfo": {"name": "abc", "address": "alamat mana saja"},
        #     "reportData": [
        #         {"test": "abc", "test2": 123},
        #         {"test": "cde", "test2": 124}
        #     ]
        # }
        self.report_has_logo = True  # sample report has logo

        data = self.get_report_values()

        return {
            "data": data,
            "config": {
                "working_date": self.working_date,
                "company": self.company_id.name,
                "user": self.env.user.name,
            }
        }

    def get_report_values2(self):
        cr = self.env.cr

        query = """
            with z_outlet_summary as (
            select pct."name" as pos_category 
                ,pc."name" as product_category	
                ,pt."name" as product
                ,case when aj.is_officer_check = true or aj.is_department_expense = true then 'OC/DE'
                 when aj.is_bank_edc_credit_card = true then 'CREDIT CARD'
                 else aj."name" end as payment
                ,pol.service_amount
                ,pol.tax_amount
                ,pol.price_subtotal	
                ,pol.price_subtotal_incl
                ,case when aj.is_officer_check = true or aj.is_department_expense = true then 'PAX' 
                 when po.is_hotel_guest = true then 'IN'
                 else 'OUT' end as cover
                ,coalesce(mtl.meal_type, 'Other') as meal_type 
            from pos_session ps
            left join pos_order po on ps.id = po.session_id
            left join meal_time_line mtl on mtl.id = po.meal_time_line_id
            left join pos_order_line pol on po.id = pol.order_id
            left join product_product pp on pol.product_id = pp.id
            left join product_template pt on pp.product_tmpl_id = pt.id
            left join product_category pc on pt.categ_id = pc.id
            left join pos_category pct on pt.pos_categ_id = pct.id
            left join account_bank_statement_line absl on absl.pos_statement_id = po.id
            left join account_bank_statement abs on absl.statement_id = abs.id
            left join account_journal aj on absl.journal_id = aj.id
            where working_date = %s
            and po.company_id = %s
            and po.state in  ('paid', 'done')
            )            
            select pos_category, '01' || left(product_category,1) as seq, product_category, SUM(price_subtotal) as price_subtotal, meal_type from z_outlet_summary
            group by pos_category, product_category, meal_type
            union
            select pos_category, '01F', 'Food', 0, meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '01FC', 'Food Cover', 0, meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '01B', 'Beverage', 0, meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '01BC', 'Beverage Cover', 0, meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '01O', 'Other', 0, meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '01' || left(product_category,1) || 'C', product_category || ' Cover', COUNT(product_category), meal_type from z_outlet_summary
            where product_category != 'Other'
            group by pos_category, product_category, meal_type
            union
            select pos_category, '03S', 'Service', SUM(service_amount), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union 
            select pos_category, '04T', 'Tax', SUM(tax_amount), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union 
            select pos_category, '05T', 'Total', SUM(price_subtotal_incl), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '06' || left(payment,2), payment , SUM(price_subtotal_incl), meal_type from z_outlet_summary
            group by pos_category, payment, meal_type
            union
            select pos_category, '07I', 'IN' , SUM(case when cover = 'IN' then 1 else 0 end), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '08O', 'OUT' , SUM(case when cover = 'OUT' then 1 else 0 end), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '09P', 'PAX' , SUM(case when cover = 'PAX' then 1 else 0 end), meal_type from z_outlet_summary
            group by pos_category, meal_type
            union
            select pos_category, '10T', 'Total Pax' , COUNT(cover), meal_type from z_outlet_summary
            group by pos_category, meal_type
            order by pos_category, seq, product_category;
        """

        params = (self.working_date, self.company_id.id)
        self._cr.execute(query, params)
        res = cr.dictfetchall()

        response = self.env['pos.helpers'].get_outlet_revenue(self.working_date)

        # {
        #     "HotelId": 38,
        #     "SubdepartmentId": 134,
        #     "ItemType": "B",
        #     "TrxDate": "2019-09-05T00:00:00",
        #     "SubdepartmentDescription": "@XPRESS",
        #     "Amount": 66116.0000,
        #     "ServiceAmount": 6612.0000,
        #     "TaxAmount": 7272.0000,
        #     "NetAmount": 80000.0000,
        #     "Cover": 0,
        #     "Pax": 0
        # }
        if response:
            payment = ''
            for r in response:
                # search charge room
                payment = self.env['account.journal'].search([
                    ('is_charge_room', '=', True),
                    ('company_id.hotel_id', '=', r['HotelId']),
                ])
            for r in response:

                # search pos_categories
                pos_categories = self.env['pos.category.mapping'].search([
                    ('company_id.hotel_id', '=', r['HotelId']),
                    ('pms_sub_department_id', '=', r['SubdepartmentId']),
                ])

                if r['ItemType'] == 'F':
                    seq = '01F'
                    product = 'Food'
                elif r['ItemType'] == 'B':
                    seq = '01B'
                    product = 'Beverage'
                else:
                    seq = '01O'
                    product = 'Other'

                outlet = pos_categories[0].pos_category_id.name if pos_categories[0].id else ''

                res.append({
                    "pos_category": outlet,
                    "seq": seq,
                    "product_category": product,
                    "price_subtotal": r['Amount'],
                    "meal_type": 'Coupon',
                })

                if product != 'Other':
                    res.append({
                        "pos_category": outlet,
                        "seq": seq + 'C',
                        "product_category": product + ' Cover',
                        "price_subtotal": r['Cover'],
                        "meal_type": 'Coupon',
                    })

                res.append({
                    "pos_category": outlet,
                    "seq": '03S',
                    "product_category": 'Service',
                    "price_subtotal": r['ServiceAmount'],
                    "meal_type": 'Coupon',
                })

                res.append({
                    "pos_category": outlet,
                    "seq": '04T',
                    "product_category": 'Tax',
                    "price_subtotal": r['TaxAmount'],
                    "meal_type": 'Coupon',
                })

                res.append({
                    "pos_category": outlet,
                    "seq": '05T',
                    "product_category": 'Total',
                    "price_subtotal": r['NetAmount'],
                    "meal_type": 'Coupon',
                })

                res.append({
                    "pos_category": outlet,
                    "seq": '06' + payment[0].name[:2],
                    "product_category": payment[0].name,
                    "price_subtotal": r['NetAmount'],
                    "meal_type": 'Coupon',
                })

                res.append({
                    "pos_category": outlet,
                    "seq": '07I',
                    "product_category": 'IN',
                    "price_subtotal": r['Pax'],
                    "meal_type": 'Coupon',
                })

                res.append({
                    "pos_category": outlet,
                    "seq": '10T',
                    "product_category": 'Total Pax',
                    "price_subtotal": r['Pax'],
                    "meal_type": 'Coupon',
                })

        return res

    def get_report_values(self):
        cr = self.env.cr

        query = """
            with z_init_product as (
            select distinct main_parent as product 
                from product_category
                where main_parent in ('BEVERAGE', 'FOOD', 'OTHER')
            ),
            z_outlet_summary as (
            select pct."name" as pos_category 
                ,hd."name" as dept_name
                ,pc.main_parent as product_category	
                ,pt."name" as product    
                ,pol.service_amount
                ,pol.tax_amount
                ,pol.price_subtotal	
                ,pol.price_subtotal_incl    
                ,coalesce(mtl.meal_type, 'Other') as meal_type 
                ,customer_count
                ,po.id
                ,working_date
                ,pol.qty
                ,pol.id    
            from pos_session ps
            left join pos_order po on ps.id = po.session_id
            left join meal_time_line mtl on mtl.id = po.meal_time_line_id
            left join pos_order_line pol on po.id = pol.order_id
            left join product_product pp on pol.product_id = pp.id
            left join product_template pt on pp.product_tmpl_id = pt.id
            left join product_category pc on pt.categ_id = pc.id
            left join pos_category pct on po.outlet_id = pct.id
            left join pos_category_mapping pcm on pct.id = pcm.pos_category_id and pcm.company_id = po.company_id
            left join hr_department hd on pcm.department_id = hd.id
            where working_date =  %s
            and po.company_id = %s
            and po.state in  ('paid', 'done')            
            ),
            z_payment_summary as (
            select pct."name" as pos_category 
                ,hd."name" as dept_name
                ,case when aj.is_officer_check = true or aj.is_department_expense = true then 'OC/DE'
                 when pg.short_name = 'CASH' then 'Cash'
                 when pg.short_name = 'CRCD' then 'Credit Card'
                 else aj."name" end as payment    
                ,case when po.is_hotel_guest = true then 'IN'
                 else 'OUT' end as cover
                ,case when aj.is_officer_check = true or aj.is_department_expense = true then 'PAX'      
                 else 'IN/OUT' end as cover_pax 
                ,coalesce(mtl.meal_type, 'Other') as meal_type 
                ,po.customer_count
                ,po.id
                ,working_date    
                ,absl.amount
            from pos_session ps
            left join pos_order po on ps.id = po.session_id
            left join meal_time_line mtl on mtl.id = po.meal_time_line_id
            left join pos_category pct on po.outlet_id = pct.id
            left join pos_category_mapping pcm on pct.id = pcm.pos_category_id and pcm.company_id = po.company_id
            left join hr_department hd on pcm.department_id = hd.id
            left join account_bank_statement_line absl on absl.pos_statement_id = po.id
            left join account_bank_statement abs on absl.statement_id = abs.id
            left join account_journal aj on absl.journal_id = aj.id
            left join journal_payment_group pg on pg.id = aj.journal_payment_group_id
            where working_date = %s
            and po.company_id = %s
            and po.state in  ('paid', 'done')
            ),  
            z_pax_summary as (
                select pos_category
                    ,dept_name
                    ,cover
                    ,cover_pax
                    ,customer_count
                    ,meal_type
                    ,id 
                from z_payment_summary
                group by pos_category
                    ,dept_name
                    ,cover
                    ,cover_pax
                    ,meal_type
                    ,customer_count
                    ,id 
            ),
            z_outlet_trx_summary as (
            select pos_category, dept_name, '1sub' as sub, '1item' as item, product_category
                ,SUM(case when meal_type = 'Coupon' then price_subtotal else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' then price_subtotal else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' then price_subtotal else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' then price_subtotal else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' then price_subtotal else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' then price_subtotal else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' then price_subtotal else 0 end) as Other
            from z_outlet_summary
            group by pos_category, dept_name, product_category
            union
            select pos_category, dept_name, '1sub' as sub, '2item' as item, 'Service'
                ,SUM(case when meal_type = 'Coupon' then service_amount else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' then service_amount else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' then service_amount else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' then service_amount else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' then service_amount else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' then service_amount else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' then service_amount else 0 end) as Other
            from z_outlet_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '1sub' as sub, '3item' as item, 'Tax'
                ,SUM(case when meal_type = 'Coupon' then tax_amount else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' then tax_amount else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' then tax_amount else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' then tax_amount else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' then tax_amount else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' then tax_amount else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' then tax_amount else 0 end) as Other
            from z_outlet_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '2sub' as sub, '1item' as item, payment
                ,SUM(case when meal_type = 'Coupon' then amount else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' then amount else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' then amount else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' then amount else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' then amount else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' then amount else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' then amount else 0 end) as Other
            from z_payment_summary
            group by pos_category, dept_name, payment
            union
            select pos_category, dept_name, '3sub' as sub, '1item' as item, 'Beverage Cover'
                ,coalesce(SUM(case when meal_type = 'Coupon' and product_category = 'BEVERAGE' then qty end),0) as Coupon
                ,coalesce(SUM(case when meal_type = 'Breakfast' and product_category = 'BEVERAGE' then qty end),0) as Breakfast
                ,coalesce(SUM(case when meal_type = 'Brunch' and product_category = 'BEVERAGE' then qty end),0) as Brunch
                ,coalesce(SUM(case when meal_type = 'Lunch' and product_category = 'BEVERAGE' then qty end),0) as Lunch
                ,coalesce(SUM(case when meal_type = 'Dinner' and product_category = 'BEVERAGE' then qty end),0) as Dinner
                ,coalesce(SUM(case when meal_type = 'Supper' and product_category = 'BEVERAGE' then qty end),0) as Supper
                ,coalesce(SUM(case when meal_type = 'Other' and product_category = 'BEVERAGE' then qty end),0) as Other
            from z_outlet_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '3sub' as sub, '2item' as item, 'Food Cover'
                ,coalesce(SUM(case when meal_type = 'Coupon' and product_category = 'FOOD' then qty end),0) as Coupon
                ,coalesce(SUM(case when meal_type = 'Breakfast' and product_category = 'FOOD' then qty end),0) as Breakfast
                ,coalesce(SUM(case when meal_type = 'Brunch' and product_category = 'FOOD' then qty end),0) as Brunch
                ,coalesce(SUM(case when meal_type = 'Lunch' and product_category = 'FOOD' then qty end),0) as Lunch
                ,coalesce(SUM(case when meal_type = 'Dinner' and product_category = 'FOOD' then qty end),0) as Dinner
                ,coalesce(SUM(case when meal_type = 'Supper' and product_category = 'FOOD' then qty end),0) as Supper
                ,coalesce(SUM(case when meal_type = 'Other' and product_category = 'FOOD' then qty end),0) as Other
            from z_outlet_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '3sub' as sub, '3item' as item, 'IN'
                ,SUM(case when meal_type = 'Coupon' and cover = 'IN' then customer_count else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' and cover = 'IN' then customer_count else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' and cover = 'IN' then customer_count else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' and cover = 'IN' then customer_count else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' and cover = 'IN' then customer_count else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' and cover = 'IN' then customer_count else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' and cover = 'IN' then customer_count else 0 end) as Other
            from z_pax_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '3sub' as sub, '4item' as item, 'OUT'
                ,SUM(case when meal_type = 'Coupon' and cover = 'OUT' then customer_count else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' and cover = 'OUT' then customer_count else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' and cover = 'OUT' then customer_count else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' and cover = 'OUT' then customer_count else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' and cover = 'OUT' then customer_count else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' and cover = 'OUT' then customer_count else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' and cover = 'OUT' then customer_count else 0 end) as Other
            from z_pax_summary
            group by pos_category, dept_name
            union
            select pos_category, dept_name, '3sub' as sub, '5item' as item, 'OC / DE Pax'
                ,SUM(case when meal_type = 'Coupon' and cover_pax = 'PAX' then customer_count else 0 end) as Coupon
                ,SUM(case when meal_type = 'Breakfast' and cover_pax = 'PAX' then customer_count else 0 end) as Breakfast
                ,SUM(case when meal_type = 'Brunch' and cover_pax = 'PAX' then customer_count else 0 end) as Brunch
                ,SUM(case when meal_type = 'Lunch' and cover_pax = 'PAX' then customer_count else 0 end) as Lunch
                ,SUM(case when meal_type = 'Dinner' and cover_pax = 'PAX' then customer_count else 0 end) as Dinner
                ,SUM(case when meal_type = 'Supper' and cover_pax = 'PAX' then customer_count else 0 end) as Supper
                ,SUM(case when meal_type = 'Other' and cover_pax = 'PAX' then customer_count else 0 end) as Other
            from z_pax_summary
            group by pos_category, dept_name
            union 
            select pos_category, dept_name, '1sub', '1item', ip.product, 0,0,0,0,0,0,0
            from z_outlet_summary os
            join z_init_product ip on os.product_category != ip.product
            group by pos_category, dept_name,ip.product
            )
            select pos_category, dept_name, sub, item, product_category, sum(coupon) as coupon,sum(breakfast) as breakfast
                ,sum(brunch) as brunch,sum(lunch) as lunch,sum(dinner) as dinner,sum(supper) as supper,sum(other) as other
            from z_outlet_trx_summary
            group by pos_category, dept_name, sub, item, product_category
            order by pos_category, dept_name, sub, item, product_category;
        """

        params = (self.working_date, self.company_id.id, self.working_date, self.company_id.id)
        self._cr.execute(query, params)
        res = cr.dictfetchall()

        response = self.env['pos.helpers'].get_outlet_revenue(self.working_date)

        # {
        #     "HotelId": 38,
        #     "SubdepartmentId": 134,
        #     "ItemType": "B",
        #     "TrxDate": "2019-09-05T00:00:00",
        #     "SubdepartmentDescription": "@XPRESS",
        #     "Amount": 66116.0000,
        #     "ServiceAmount": 6612.0000,
        #     "TaxAmount": 7272.0000,
        #     "NetAmount": 80000.0000,
        #     "Cover": 0,
        #     "Pax": 0
        # }

        if response:
            payment = ''
            for r in response:
                # search charge room
                payment = self.env['account.journal'].search([
                    ('is_charge_room', '=', True),
                    ('company_id.hotel_id', '=', r.get('HotelId', '')),
                ])
            for r in response:
                product_list = ['BEVERAGE', 'FOOD', 'OTHER']
                # search pos_categories
                pos_categories = self.env['pos.category.mapping'].search([
                    ('company_id.hotel_id', '=', r.get('HotelId', '')),
                    ('pms_sub_department_id', '=', r.get('SubdepartmentId', '')),
                ])

                if r['ItemType'] == 'F':
                    product = product_list[1]
                    cover = 'Food Cover'
                elif r['ItemType'] == 'B':
                    product = product_list[0]
                    cover = 'Beverage Cover'
                else:
                    product = product_list[2]
                    cover = ""

                outlet = pos_categories[0].pos_category_id.name if pos_categories[0].id else ''
                department = pos_categories[0].department_id.name if pos_categories[0].id else ''
                outlet_found = False
                product_found = False
                payment_found = False
                for item in res:
                    if item.get('pos_category', '') == outlet:
                        outlet_found = True
                        if item.get('product_category', '') == product:
                            item['coupon'] += r.get('Amount', 0)
                            product_found = True
                        elif item.get('product_category', '') == payment[0].name:
                            # item['coupon'] += r['NetAmount']
                            net_amount = r.get('Amount', 0) + r.get('ServiceAmount', 0) + r.get('TaxAmount', 0)
                            item['coupon'] += net_amount
                            payment_found = True
                        elif item.get('product_category', '') == 'Service':
                            item['coupon'] += r.get('ServiceAmount', 0)
                        elif item.get('product_category', '') == 'Tax':
                            item['coupon'] += r.get('TaxAmount', 0)
                        elif item.get('product_category', '') == 'Beverage Cover' and r.get('ItemType', '') == 'B':
                            item['coupon'] += r.get('Cover', 0)
                        elif item.get('product_category', '') == 'Food Cover' and r.get('ItemType', '') == 'F':
                            item['coupon'] += r.get('Cover', 0)
                        elif item.get('product_category', '') == 'IN':
                            item['coupon'] += r.get('Pax', 0)

                if outlet_found and not product_found:
                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '1sub',
                        'item': '1item',
                        'product_category': product,
                        'coupon': r.get('Amount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                if outlet_found and not payment_found:
                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '2sub',
                        'item': '1item',
                        'product_category': payment[0].name,
                        # 'coupon': r['NetAmount'],
                        'coupon': r.get('Amount', 0) + r.get('ServiceAmount', 0) + r.get('TaxAmount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                if not outlet_found:
                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '1sub',
                        'item': '1item',
                        'product_category': product,
                        'coupon': r.get('Amount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    product_list.remove(product)

                    if len(product_list) > 0:
                        for p in product_list:
                            res.append({
                                'pos_category': outlet,
                                'dept_name': department,
                                'sub': '1sub',
                                'item': '1item',
                                'product_category': p,
                                'coupon': 0,
                                'breakfast': 0,
                                'brunch': 0,
                                'lunch': 0,
                                'dinner': 0,
                                'supper': 0,
                                'other': 0,
                            })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '1sub',
                        'item': '2item',
                        'product_category': 'Service',
                        'coupon': r.get('ServiceAmount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '1sub',
                        'item': '3item',
                        'product_category': 'Tax',
                        'coupon': r.get('TaxAmount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '2sub',
                        'item': '1item',
                        'product_category': payment[0].name,
                        # 'coupon': r['NetAmount'],
                        'coupon': r.get('Amount', 0) + r.get('ServiceAmount', 0) + r.get('TaxAmount', 0),
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '3sub',
                        'item': '1item',
                        'product_category': 'Beverage Cover',
                        'coupon': r['Cover'] if r['ItemType'] == 'B' else 0,
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '3sub',
                        'item': '2item',
                        'product_category': 'Food Cover',
                        'coupon': r['Cover'] if r['ItemType'] == 'F' else 0,
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '3sub',
                        'item': '3item',
                        'product_category': 'IN',
                        'coupon': r['Pax'],
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '3sub',
                        'item': '4item',
                        'product_category': 'OUT',
                        'coupon': 0,
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

                    res.append({
                        'pos_category': outlet,
                        'dept_name': department,
                        'sub': '3sub',
                        'item': '5item',
                        'product_category': 'OC / DE Pax',
                        'coupon': 0,
                        'breakfast': 0,
                        'brunch': 0,
                        'lunch': 0,
                        'dinner': 0,
                        'supper': 0,
                        'other': 0,
                    })

        return res

    def _define_report_name(self):
        """ path to report file)
        /app_name/path_to_file/report_name.mrt
        example: "/kg_report_base/static/rpt/RegistrationCard.mrt"
          kg_report_base is app name (module name)

        :return: str
        """

        rpt = "/kg_pos/static/rpt/OutletSummary5.mrt"

        return rpt

        # return "/kg_report_base/static/rpt/sample1.mrt"
