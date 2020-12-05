from odoo import models, api, fields


class KgReportPosBill(models.TransientModel):
    """ View Report without KG Report Wizard
    direct view KG Report - view menu Action Print (.mrt)

    """
    _inherit = 'report.kg_report_action_abstract'
    _name = 'report.kg_report_action_pos_order_bill'

    _title = "KG Report - POS Order Bill"

    @api.model
    def _define_report_name(self, doc_ids, data, records):
        if records:
            order = records[0]
            report_name = order.config_id.receipt_bill_report_name
        else:
            report_name = 'single.mrt'
        return '/kg_pos/static/rpt/{report_name}'.format(report_name=report_name)

    @api.model
    def _get_data(self, doc_ids, data, records, **kwargs):
        report_data = []
        for order in records:
            order_lines = self._format_order_lines(order)
            payment_lines, hide_service_tax = self._format_payment_lines(order)
            order.print_counter += 1
            validation_date = fields.Datetime.context_timestamp(self, fields.Datetime.from_string(
                order.date_order
            )).isoformat('T')
            current_order = {
                "order_id": order.id,
                "name": order.pos_reference,
                "config_name": order.config_id.name,
                "table_name": "TBL    " + order.table_id.name if order.table_id else "",
                "cashier_name": order.user_id.name,
                "waiter_name": order.waiter_id.name if order.waiter_id else "",
                "customer_count": order.customer_count,
                "validation_date": validation_date,
                "hide_service_tax": hide_service_tax,
                "print_counter": order.print_counter,
                "is_hotel_guest": "I" if order.is_hotel_guest else "O",
                "company_name": order.company_id.name,
                "shop_name": order.config_id.name,
                "currency_symbol": order.session_id.currency_id.symbol if order.session_id.currency_id else " ",
                "currency_rounding": order.session_id.currency_id.rounding if order.session_id.currency_id else 0.01,
                "discount": order.total_disc_amount_before_tax,
                "sub_total": order.amount_untaxed,
                "service": order.amount_service,
                "tax": order.amount_tax_only,
                "total": order.amount_total,
                "change": order.change if order.change else 0,
                "order_lines": order_lines,
                "payment_lines": payment_lines
            }
            report_data.append(current_order)
        return {
            "orders": report_data
        }

    @staticmethod
    def _format_payment_lines(order):
        payment_lines = []
        hide_service_tax = False
        for payment in order.statement_ids:
            payment_line = {
                "order_id": order.id,
                "name": payment.journal_id.name,
                "amount": payment.amount,
                "is_officer_check": payment.journal_id.is_officer_check,
                "is_department_expense": payment.journal_id.is_department_expense,
            }
            if payment.journal_id.is_department_expense or payment.journal_id.is_officer_check:
                hide_service_tax = True
                if order.department_id:
                    payment_line['name'] = "Departement: {name}".format(name=order.department_id.name)
                elif order.employee_id:
                    payment_line['name'] = "Employee: {name}".format(name=order.employee_id.name)
            payment_lines.append(payment_line)
        return payment_lines, hide_service_tax

    @staticmethod
    def _format_order_lines(order):
        order_lines = []
        for line in order.lines:
            order_line = {
                "order_id": order.id,
                "quantity": line.qty,
                "displayName": line.custom_item_name if line.custom_item_name else line.product_id.name,
                "priceWithTax": line.price_subtotal_incl,
                "priceWithoutTax": line.price_subtotal,
                "tax": line.tax_amount,
                # "taxDetails": line.tax_ids_after_fiscal_position,
                "serviceAmount": line.service_amount,
                "taxWithoutService": line.tax_amount,
                "bruttoBeforeTax": line.line_brutto_before_tax,
                "lineDiscAmountBeforeTax": line.line_disc_amount_before_tax,
                "unit_name": line.product_id.name,
                "price": line.price_unit,
                "discount": line.discount,
                "product_name": line.product_id.name,
                "product_name_wrapped": line.product_id.name,
                "main_category": line.product_id.main_category,
                "price_display": line.price_unit,
                "product_description": "",
                "note": line.note,
                "product_description_sale": ""
            }
            order_lines.append(order_line)
        return order_lines
