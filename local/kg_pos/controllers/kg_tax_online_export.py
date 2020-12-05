# -*- coding: utf-8 -*-
import functools
import json
import logging
import copy
from datetime import datetime
import werkzeug
from dateutil import parser, relativedelta
import pytz
import os
import subprocess

from odoo.addons.kg_pos.controllers.kg_api_pos_reports import parse_date, \
    json_response, invalid_response, validate_token
from odoo import http
from odoo.http import request

API_POS_TAX_ONLINE = '/kg/api/pos/order/tax-online'
API_ROUTES = [
    API_POS_TAX_ONLINE,
]
HTTP_METHOD_OPTION = "OPTIONS"


class KgApiTaxOnlineExport(http.Controller):

    @http.route(API_ROUTES, type='http', auth="none", methods=[HTTP_METHOD_OPTION], csrf=False)
    def http_options(self, **payload):
        # api with http method OPTIONS is required from javascript web client
        return json_response({}, http_method=HTTP_METHOD_OPTION)

    @http.route('/kg/api/pos/order/tax-online', auth='none',
                cors="*", type='http', methods=['GET'], csrf=False)
    @validate_token
    def get_pos_order_tax_report(self, company_id=1, date=None, format_output="txt"):
        try:
            company_id = int(company_id)
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            pos_date = parse_date(date)
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))

        # Laporan pajak online utk transaksi pos order
        data = self.get_data(http.request.env, company_id, pos_date)
        company = http.request.env['res.company'].search([('id', '=', company_id)])
        if company.region_name == 'bali' or format_output == 'bali':
            result = self.generate_for_bali(data)
        elif company.region_name == 'surabaya' or format_output == 'sby':
            result = self.generate_for_jakarta(data, format_output=format_output, show_tax_amount=True)
        elif company.region_name == 'jakarta' or format_output in ('txt', 'jkt'):
            result = self.generate_for_jakarta(data, format_output=format_output, show_tax_amount=False)
        else:
            return invalid_response(
                'user_company_config_error',
                'Region user belum di definisikan, silahkan ke konfigurasi organisasi user anda ',
                412)

        return json_response({
            'result': result
        })

    @staticmethod
    def generate_for_jakarta(
            data,
            format_output='txt',
            show_tax_amount=False,
            txt_file=None,
            worksheet=None, row_no_start_from=0
    ):
        counter_item = 0
        row_no = row_no_start_from
        prev_order_id = 0
        result = []
        for rec in data:
            tax_amount = rec.get('tax_amount', 0)
            if rec.get('price_subtotal', 0) > 0 and tax_amount > 0:
                # Reset counter if order id changed
                if rec.get('order_id', 0) != prev_order_id:
                    prev_order_id = rec.get('order_id', 0)
                    counter_item = 1
                else:
                    counter_item += 1
                ref = rec.get('pos_name', '').split('/')
                bill_no = ref[-1]  # ambil nomor counter pos bill (element terakhir dari array ref)

                receipt_no = rec.get('config_name', '') + ' ' + bill_no
                transaction_id = receipt_no + str(counter_item) + 'Z'
                working_date = datetime.strftime(parser.parse(rec.get('working_date')), '%Y%m%d%H%M%S')
                tax_code = rec.get('tax_code')
                description = rec.get('product_name', '').replace('"', '')
                # description = rec.get('tax_category', '').replace('"', '')
                price_subtotal = rec.get('price_subtotal', 0)
                amount = int_to_str(price_subtotal)
                flag = '1' if tax_amount != 0 else '0'

                service_amount = int(rec.get('service_amount', 0))
                tax_for_service, tax_for_item = calculate_tax(price_subtotal, service_amount, tax_amount)

                row_data = KgApiTaxOnlineExport.format_row_and_write_to_file(
                    row_no, working_date,
                    transaction_id, receipt_no, amount, description, flag, tax_code,
                    tax_amount=tax_for_item,
                    worksheet=worksheet, txt_file=txt_file,
                    show_tax_amount=show_tax_amount, format_output=format_output)

                result.append(row_data)

                if service_amount > 0:
                    transaction_id = receipt_no + str(counter_item) + 'V'
                    tax_code = 'ATV'
                    description = 'Service Charge'
                    amount = int_to_str(service_amount)
                    flag = '1' if service_amount != 0 else '0'
                    row_no += 1
                    row_data = KgApiTaxOnlineExport.format_row_and_write_to_file(
                        row_no, working_date,
                        transaction_id, receipt_no, amount, description, flag, tax_code,
                        tax_amount=tax_for_service,
                        worksheet=worksheet, txt_file=txt_file,
                        show_tax_amount=show_tax_amount, format_output=format_output)

                    result.append(row_data)

            row_no += 1

        return result

    @staticmethod
    def format_row_and_write_to_file(
            row_no, working_date,
            transaction_id, receipt_no, amount, description, flag, tax_code, tax_amount,
            worksheet=None, txt_file=None, show_tax_amount=None, format_output=None
    ):
        if format_output != 'txt' or worksheet:
            # format not text --> expect dictionary, or output to excel
            row_data = KgApiTaxOnlineExport.jakarta_dict(
                show_tax_amount,
                transaction_id, receipt_no, tax_code, working_date, description, amount, flag,
                int_to_str(tax_amount))
        else:
            # if text file and not excel (worksheet None)
            row_data = KgApiTaxOnlineExport.jakarta_row(
                show_tax_amount,
                transaction_id, receipt_no, tax_code, working_date, description, amount, flag,
                int_to_str(tax_amount))
        if txt_file:
            txt_file.write(row_data + "\n")
        elif worksheet:
            KgApiTaxOnlineExport.write_excel(row_no, row_data, worksheet)
        return row_data

    @staticmethod
    def jakarta_dict(show_tax_amount, transaction_id, receipt_no, tax_code, working_date, description,
                     amount, flag, tax_amount):
        return {
            'trx_id': transaction_id,
            'receipt_no': receipt_no,
            'tax_code': tax_code,
            'trx_date2': working_date,
            'description': description,
            'amount': amount,
            'flag': flag,
            'tax_amount': tax_amount
        }

    @staticmethod
    def write_excel(row_no, row_data, worksheet):
        worksheet.write(row_no, 0, row_data.get('trx_id'))
        worksheet.write(row_no, 1, row_data.get('receipt_no'))
        worksheet.write(row_no, 2, row_data.get('tax_code'))
        worksheet.write(row_no, 3, row_data.get('trx_date2'))
        worksheet.write(row_no, 4, row_data.get('description'))
        worksheet.write(row_no, 5, row_data.get('amount'))
        worksheet.write(row_no, 6, row_data.get('flag'))
        worksheet.write(row_no, 7, row_data.get('tax_amount'))

    @staticmethod
    def jakarta_row(
            show_tax_amount, transaction_id, receipt_no, tax_code, working_date, description,
            amount, flag, tax_amount):

        row_data = '"' + transaction_id + '"|'
        row_data += '"' + receipt_no + '"|'
        row_data += '"' + tax_code + '"|'
        row_data += '"' + working_date + '"|'
        row_data += '"' + description + '"|'
        row_data += '"' + amount + '"|'
        row_data += '"' + flag + '"'
        if show_tax_amount:
            row_data += '"' + tax_amount + '"'
        return row_data

    @staticmethod
    def generate_for_bali(data, txt_file=None):
        prev_order_id = 0
        product_list = ""
        first_part = ""
        last_part = ""
        result = []
        price_subtotal = 0
        service_amount = 0
        tax_amount = 0
        price_subtotal_incl = 0
        for rec in data:
            if rec.get('order_id', 0) == prev_order_id or prev_order_id == 0:
                product_list = product_list + "|" if product_list else product_list
                product_list += "{product_name}^{quantity}^{price}".format(
                    product_name=rec.get('product_name', '').replace('"', '').replace("|", ""),
                    quantity=int_to_str(rec.get('qty', '')),
                    price=int_to_str(rec.get('price_unit', ''))
                )
            else:
                # pergantian order id
                # write row data utk order id sebelumnya
                if tax_amount > 0:
                    row_data = first_part + product_list + ';' + last_part
                    result.append(row_data)
                # reset variables
                product_list = ""
                counter_item = 1
                prev_order_id = rec.get('order_id', 0)
                price_subtotal = 0
                service_amount = 0
                tax_amount = 0
                price_subtotal_incl = 0

            # prepare data utk order id yg baru
            ref = rec.get('pos_name', '').split('/')
            bill_no = ref[-1]  # ambil nomor counter pos bill (element terakhir dari array ref)

            receipt_no = rec.get('config_name', '') + ' ' + bill_no
            # transaction_id = receipt_no + str(counter_item) + 'Z'
            tax_code = rec.get('tax_code')

            price_subtotal += round(rec.get('price_subtotal', ''), 0)
            service_amount += round(rec.get('service_amount', ''), 0)
            tax_amount += int(rec.get('tax_amount', '0'))
            price_subtotal_incl += round(rec.get('price_subtotal_incl', ''), 0)

            working_date = datetime.strftime(parser.parse(rec.get('working_date')), '%Y%m%d')
            date_order = parser.parse(rec.get('date_order'))
            # date_combine => date = working date, time = pos order time
            date_combine = parser.parse("{working_date} {time}".format(
                working_date=working_date,
                time=datetime.strftime(date_order, '%H:%M:%S')))

            timezone_bali = 'Asia/Makassar'
            utc_timestamp = pytz.utc.localize(date_combine, is_dst=False)
            bali_datetime = utc_timestamp.astimezone(pytz.timezone(timezone_bali))

            first_part = datetime.strftime(bali_datetime, '%Y/%m/%d') + ';'
            first_part += receipt_no + ';'
            first_part += receipt_no + ';'
            first_part += tax_code + ';'
            first_part += datetime.strftime(bali_datetime, '%m/%d/%Y %H:%M') + ';'
            first_part += rec.get('config_name', '') + ';'
            first_part += int_to_str(price_subtotal) + ';'  # subtotal without (before) tax/service
            first_part += '1;' if tax_amount else '0;'
            first_part += 'VER 2' + ';'
            first_part += int_to_str(price_subtotal) + ';'
            first_part += '0' + ';'
            first_part += int_to_str(service_amount) + ';'
            first_part += int_to_str(tax_amount) + ';'
            first_part += int_to_str(price_subtotal_incl) + ';'

            last_part = datetime.strftime(bali_datetime, '%d/%m/%Y %H:%M:%S') + ' +0800' + ';'
            last_part += ';'
            last_part += ';'

        # write row data utk order terakhir
        if tax_amount > 0:
            row_data = first_part + product_list + ';' + last_part
            result.append(row_data)
            if txt_file:
                txt_file.write(row_data + "\n")

        return result

    @staticmethod
    def get_data(env, company_id, pos_date):
        query = """
            select s.id as session_id, po.id as order_id, s.working_date, pol.id as line_id
            , c.name as config_name, po.name as pos_name, po.date_order
            , coalesce(tc.tax_code, 'ATM') as tax_code
            , coalesce(tc.tax_category, 'Makan/Minum') as tax_category
            , pt.name as product_name
            , pol.qty, pol.price_unit
            , pol.price_subtotal, pol.price_subtotal_incl
            , service_amount
            , tax_amount
            From
            pos_session s
            left join pos_config c on c.id = s.config_id
            left join pos_order po on po.session_id = s.id
            left join pos_order_line pol on pol.order_id = po.id
            left join product_product pp on pp.id = pol.product_id
            left join product_template pt on pt.id = pp.product_tmpl_id
            left join tax_category tc on tc.id = pt.tax_category_id
            where 
            -- s.state = 'closed' and
            s.working_date = '{pos_date}' and 
            po.company_id = {company_id} and
            po.state != 'draft' and po.state != 'cancel' 
            and po.department_id is null and po.employee_id is null            
            order by s.id, po.id, pol.id
            """.format(company_id=company_id, pos_date=pos_date)
        env.cr.execute(query)
        pos_trx_summary = env.cr.dictfetchall()
        return pos_trx_summary


def int_to_str(var):
    return str(var).replace(".0", "")


def calculate_tax(price_subtotal, service_amount, tax_amount):
    tax_for_service = 0
    if service_amount == 0:
        tax_for_item = tax_amount
    else:
        pct_tax = float(tax_amount) / float(price_subtotal + service_amount)
        tax_for_item = round(pct_tax * price_subtotal, 0)
        tax_for_service = tax_amount - tax_for_item
    return tax_for_service, tax_for_item

