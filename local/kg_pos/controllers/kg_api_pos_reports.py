# -*- coding: utf-8 -*-
import functools
import json
import logging
import copy
from datetime import datetime
import werkzeug
from dateutil import parser, relativedelta
import os
import subprocess

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)
HTTP_METHOD_OPTION = "OPTIONS"


def get_git_revisions_hash(path):
    try:
        # repo = git.Repo(path, search_parent_directories=True)
        # latest_git_commit_sha = repo.head.object.hexsha
        rev = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path)
        # hashes.append(subprocess.check_output(['git', 'rev-parse', 'HEAD^'], cwd=path))
        return rev.decode("utf-8") if rev else ""
    except Exception as ex:
        return ""


def json_response(data, status=200, http_method=None):
    """Valid Response
    This will be return when the http request was successfully processed."""
    response = werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data),
    )
    if http_method == HTTP_METHOD_OPTION:
        # set CORS utk http request dg method options
        # krn default cors-nya mengeset allow header yg terbatas, terpaksa di set manual lg
        set_response_headers(response)
    return response


def set_response_headers(response):
    # not needed anymore, simply set cors="*" on @http.route decorator
    #   these 2 line will automatically added
    response.headers['Access-Control-Allow-Origin'] = "*"
    # response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"

    # response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "Origin, access-token, access_token, " \
                                                       "cache-control, Authorization, " \
                                                       "X-Requested-With, Content-Type, Accept, X-Debug-Mode,"
    # response.headers["Access-Control-Expose-Headers"] = "*"
    return response


def invalid_response(typ, message=None, status=400):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps({
            'type': typ,
            'message': message if message else 'wrong arguments (missing validation)',
        }),
    )


def validate_token(func):
    """."""
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get('access_token')
        if not access_token:
            access_token = request.httprequest.headers.get('Authorization')
        if not access_token:
            return invalid_response('access_token_not_found', 'missing access token in request header', 401)
        access_token_data = request.env['api.access_token'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response('access_token', 'token seems to have expired or invalid', 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)
    return wrap


def parse_date(date):
    # validate date from url query params
    if date:
        date_filter = parser.parse(date)
    else:
        date_filter = datetime.now()
    return date_filter.isoformat()[:10]  # get yyyy-MM-dd


def get_last_year_month_to_date(month_start_date, pos_date):
    start_date = parser.parse(month_start_date)
    end_date = parser.parse(pos_date)
    last_year_start_date = start_date - relativedelta.relativedelta(years=1)
    last_year_end_date = end_date - relativedelta.relativedelta(years=1)
    return last_year_start_date.isoformat()[:10], last_year_end_date.isoformat()[:10]


API_MANAGER_REPORT_URL = '/kg/api/pos/report/manager-report'
API_DAILY_REVENUE_URL = '/kg/api/pos/report/daily-revenue'
API_DAILY_CARD_URL = '/kg/api/pos/report/daily-card'
API_OPEN_SESSION_URL = '/kg/api/pos/report/open-session'
API_POS_PAYMENT_DETAILS_URL = '/kg/api/pos/report/pos-payment-details'
API_VOUCHER_STATISTIC_URL = '/kg/api/pos/report/voucher-statistic'
API_POINT_HISTORY_URL = '/kg/api/pos/report/point-history'
API_ROUTES = [
    API_MANAGER_REPORT_URL,
    API_DAILY_REVENUE_URL,
    API_DAILY_CARD_URL,
    API_OPEN_SESSION_URL,
    API_POS_PAYMENT_DETAILS_URL,
    API_VOUCHER_STATISTIC_URL,
    API_POINT_HISTORY_URL,
]


class KgApiReport(http.Controller):

    @http.route('/kg/api/health-check', auth='public',
                cors="*", type='http', methods=['GET'], csrf=False)
    def health_check(self):
        path = os.path.join(os.getcwd().replace('server', '').replace('custom', ''), 'custom')
        latest_git_commit_sha = get_git_revisions_hash(path)
        return json_response({
            "status": "OK",
            "version": "11.0.1.00001-a",
            "git": {
                # check di command prompt: git rev-parse HEAD
                "latest_commit_sha": latest_git_commit_sha,
                "path": path or os.getcwd(),
            }
        })

    @http.route('/kg/api/pos/report/hello', auth='public',
                cors="*", type='http', methods=['GET'], csrf=False)
    def hello(self):
        return json_response({
            "say": "Hello, world",
        })

    @http.route(API_ROUTES, type='http', auth="none", methods=[HTTP_METHOD_OPTION], csrf=False)
    def http_options(self, **payload):
        # api with http method OPTIONS is required from javascript web client
        return json_response({}, http_method=HTTP_METHOD_OPTION)

    @http.route(API_MANAGER_REPORT_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_manager_report(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            pos_date = parse_date(kwargs.get('date', None))
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))
        try:
            today_summary = get_pos_data_group_by_product_category(
                company_id=company_id, pos_date=pos_date, pos_date_end=pos_date)
            # month to date
            month_start_date = pos_date[:7] + '-01'
            mtd_summary = get_pos_data_group_by_product_category(
                company_id=company_id, pos_date=month_start_date, pos_date_end=pos_date)
            # year to date
            year_start_date = pos_date[:4] + '-01-01'
            ytd_summary = get_pos_data_group_by_product_category(
                company_id=company_id, pos_date=year_start_date, pos_date_end=pos_date)

            results = []
            for data in ytd_summary:
                today_amount = 0
                # today_amount_include_tax = 0
                for today_data in today_summary:
                    if today_data.get('category_id') == data.get('category_id'):
                        today_amount = today_data.get('subtotal_without_tax', 0)
                        # today_amount_include_tax = today_data.get('subtotal_include_tax')
                mtd_amount = 0
                # mtd_amount_include_tax = 0
                for mtd_data in mtd_summary:
                    if mtd_data.get('category_id') == data.get('category_id'):
                        mtd_amount = mtd_data.get('subtotal_without_tax', 0)
                        # mtd_amount_include_tax = mtd_data.get('subtotal_include_tax')

                results.append({
                    'category_name': data.get('category_name'),
                    'today': today_amount,
                    'month_to_date': mtd_amount,
                    'year_to_date': data.get('subtotal_without_tax')
                })

            return json_response({
                "company_id": company_id,
                "date": pos_date,
                "data": results})

        except Exception as ex:
            return invalid_response('Failed to retrieve data', str(ex))

    @http.route(API_DAILY_REVENUE_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_daily_revenue(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            pos_date = parse_date(kwargs.get('date', None))
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))
        try:
            today_summary = get_pos_data_daily_revenue(
                company_id=company_id, pos_date=pos_date, pos_date_end=pos_date)
            # month to date
            month_start_date = pos_date[:7] + '-01'
            mtd_summary = get_pos_data_daily_revenue(
                company_id=company_id, pos_date=month_start_date, pos_date_end=pos_date)
            # month to date last year
            start_date, end_date = get_last_year_month_to_date(month_start_date, pos_date)
            mtd_last_year_summary = get_pos_data_daily_revenue(
                company_id=company_id, pos_date=start_date, pos_date_end=end_date)

            # crosscheck mtd_last_year_summary vs mtd_summary, insert ke mtd_last_year_summary yg belum ada
            for mtd_data in mtd_summary:
                if not any(data.get('category_id') == mtd_data.get('category_id') and
                           data.get('outlet_id') == mtd_data.get('outlet_id')
                           for data in mtd_last_year_summary):
                    new_data = copy.deepcopy(mtd_data)
                    new_data['subtotal_without_tax'] = 0
                    new_data['subtotal_include_tax'] = 0
                    mtd_last_year_summary.append(new_data)

            # create final data summary
            results = []
            for data in mtd_last_year_summary:
                today_amount = 0
                # today_amount_include_tax = 0
                for today_data in today_summary:
                    if today_data.get('category_id') == data.get('category_id'):
                        today_amount = today_data.get('subtotal_without_tax', 0)
                        # today_amount_include_tax = today_data.get('subtotal_include_tax')
                mtd_amount = 0
                # mtd_amount_include_tax = 0
                for mtd_data in mtd_summary:
                    if mtd_data.get('category_id') == data.get('category_id'):
                        mtd_amount = mtd_data.get('subtotal_without_tax', 0)
                        # mtd_amount_include_tax = mtd_data.get('subtotal_include_tax')

                results.append({
                    'outlet_id': data.get('outlet_id'),
                    'outlet_name': data.get('outlet_name'),
                    'category_id': data.get('category_id'),
                    'category_name': data.get('category_name'),
                    'today': today_amount,
                    'month_to_date': mtd_amount,
                    'month_to_date_last_year': data.get('subtotal_without_tax', 0),
                    'variance': mtd_amount - data.get('subtotal_without_tax', 0)
                })

            return json_response({
                "company_id": company_id,
                "date": pos_date,
                "data": results})

        except Exception as ex:
            return invalid_response('Failed to retrieve data', str(ex))

    @http.route(API_DAILY_CARD_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_daily_card(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            pos_date = parse_date(kwargs.get('date', None))
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))

        try:
            data = get_pos_data_daily_card(company_id, pos_date)
        except Exception as ex:
            return invalid_response('Error!', str(ex))

        return json_response({
                "company_id": company_id,
                "date": pos_date,
                "data": data})

    @http.route(API_OPEN_SESSION_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_open_session(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            working_date = parse_date(kwargs.get('date', None))
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))

        try:
            data = get_pos_data_open_session(company_id, working_date)
        except Exception as ex:
            return invalid_response('Error!', str(ex))

        return json_response({
            "company_id": company_id,
            "working_date": working_date,
            "data": data
        })

    @http.route(API_VOUCHER_STATISTIC_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_voucher_statistic(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            working_date = parse_date(kwargs.get('working_date', None))
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))
        try:
            data = get_pos_data_voucher_statistic(company_id, working_date)
        except Exception as ex:
            return invalid_response('Error!', str(ex))

        return json_response({
            "company_id": company_id,
            "working_date": working_date,
            "data": data
        })

    @http.route(API_POINT_HISTORY_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_history_point_transaction(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            start_date = parse_date(kwargs.get('start_date', None))
        except Exception as ex:
            return invalid_response('Parameter start date is invalid!', str(ex))
        try:
            end_date = parse_date(kwargs.get('end_date', None))
        except Exception as ex:
            return invalid_response('Parameter end date is invalid!', str(ex))
        try:
            point_type = str(kwargs.get('point_type', None))
        except Exception as ex:
            return invalid_response('Parameter point type is invalid!', str(ex))
        try:
            data = get_history_point_transaction(company_id, start_date, end_date, point_type)
        except Exception as ex:
            return invalid_response('Error!', str(ex))

        return json_response({
            "company_id": company_id,
            "start_date": start_date,
            "end_date": end_date,
            "point_type": point_type,
            "data": data
        })

    @http.route(API_POS_PAYMENT_DETAILS_URL,
                type='http', auth="none", methods=['GET'], cors="*", csrf=False)
    @validate_token
    def get_pos_payment_details(self, *args, **kwargs):
        try:
            company_id = int(kwargs.get('company_id', 1))
        except Exception as ex:
            return invalid_response('Parameter company_id is invalid!', str(ex))
        try:
            start_working_date = parse_date(kwargs.get('start_date', None))
        except Exception as ex:
            return invalid_response('Parameter start date is invalid!', str(ex))
        try:
            end_working_date = parse_date(kwargs.get('end_date', None))
            if end_working_date < start_working_date:
                return invalid_response('End working date is smaller than start working date!')
        except Exception as ex:
            return invalid_response('Parameter date is invalid!', str(ex))
        try:
            pms_payment_type = str(kwargs.get('pms_payment_type', 1))
        except Exception as ex:
            return invalid_response('Parameter payment type is invalid!', str(ex))
        try:
            if len(pms_payment_type) <= 3:
                data = get_pos_data_pos_payment_details(company_id, start_working_date, end_working_date,
                                                        pms_payment_type)
            else:
                return invalid_response('Error!', str("PMS payment type length can't be more than 3."))
        except Exception as ex:
            return invalid_response('Error!', str(ex))

        return json_response({
            "company_id": company_id,
            "start_date": start_working_date,
            "end_date": end_working_date,
            "pms_payment_type": pms_payment_type,
            "data": data
        })


def get_pos_data_group_by_product_category(company_id, pos_date, pos_date_end):
    # get pos transaction data for Manager Report
    query = """
        select pc.id as category_id, pc.name as category_name
        , sum(pol.price_subtotal) as subtotal_without_tax
        , sum(pol.price_subtotal_incl) as subtotal_include_tax
        From
        pos_session s
        left join pos_order po on po.session_id = s.id
        left join pos_order_line pol on pol.order_id = po.id
        left join product_product pp on pp.id = pol.product_id
        left join product_template pt on pt.id = pp.product_tmpl_id
        left join product_category pc on pc.id = pt.categ_id
        where 
        s.state = 'closed' and
        -- s.start_at between '{pos_date}T00:00:00+07:00' and '{pos_date_end}T23:59:59+07:00' and
        s.working_date between '{pos_date}' and '{pos_date_end}' and
        po.company_id = {company_id} and
        po.state != 'draft' and po.state != 'cancel' 
        and po.department_id is null and po.employee_id is null
        group by pc.id, pc.name
        order by pc.name
        """.format(company_id=company_id, pos_date=pos_date, pos_date_end=pos_date_end)
    # po.state != 'draft' and po.state != 'cancel'
    # transaksi utk department_id expense dan office check tidak boleh diikutkan di summary ini
    # and po.department_id is null and po.employee_id is null

    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    pos_trx_summary = http.request.env.cr.dictfetchall()

    return pos_trx_summary


def get_pos_data_daily_revenue(company_id, pos_date, pos_date_end):
    # get pos transaction data for Daily Revenue Report
    query = """
        select 
        posc.id as outlet_id, posc.name as outlet_name 
        , pc.id as category_id, pc.name as category_name
        , sum(pol.price_subtotal) as subtotal_without_tax
        , sum(pol.price_subtotal_incl) as subtotal_include_tax
        From
        pos_session s
        left join pos_order po on po.session_id = s.id
        left join pos_order_line pol on pol.order_id = po.id
        left join product_product pp on pp.id = pol.product_id
        left join product_template pt on pt.id = pp.product_tmpl_id
        left join product_category pc on pc.id = pt.categ_id
        left join pos_category posc on posc.id = pt.pos_categ_id
        where 
        s.state = 'closed' and
        -- s.start_at between '{pos_date}T00:00:00+07:00' and '{pos_date_end}T23:59:59+07:00' and
        s.working_date between '{pos_date}' and '{pos_date_end}' and
        po.company_id = {company_id} and
        po.state != 'draft' and po.state != 'cancel' 
        and po.department_id is null and po.employee_id is null
        group by posc.id, posc.name, pc.id, pc.name
        order by posc.name, pc.name
        """.format(company_id=company_id, pos_date=pos_date, pos_date_end=pos_date_end)
    # po.state != 'draft' and po.state != 'cancel'
    # transaksi utk department_id expense dan office check tidak boleh diikutkan di summary ini
    # and po.department_id is null and po.employee_id is null

    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    pos_trx_summary = http.request.env.cr.dictfetchall()

    return pos_trx_summary


def get_pos_data_daily_card(company_id, pos_date):
        # get pos transaction data for Daily Card Report
        query = """
            select s.working_date as TrxDate, 
                case when posc.name is null then 'NA' else posc.name end as ItemType, 
                0 as SubdepartmentId, 
                sum(pol.price_subtotal_incl) as Amount, 
                1 as DebitCredit, 
                case when posc.name is null then 'NA' else posc.name end as Description, 
                'NET SALES' as RowGroup, 
                1 as RowOrder1, 
                row_number() over()+10 as RowOrder2 
            From pos_session s left join pos_order po on po.session_id = s.id
                left join pos_order_line pol on pol.order_id = po.id
                left join product_product pp on pp.id = pol.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                left join product_category pc on pc.id = pt.categ_id
                left join pos_category posc on posc.id = pt.pos_categ_id
            where s.working_date = '{pos_date}' and
                po.company_id = {company_id} and
                -- s.state = 'closed' and
                po.state not in ('draft', 'cancel')
                and po.employee_id is null and po.department_id is null 
                and posc.id is not null
            group by s.working_date, posc.name
            union
            select s.working_date as TrxDate, 
                pc.name as ItemType, 
                0 as SubdepartmentId, 
                abs(sum(pol.price_subtotal_incl)) as Amount, 
                -1 as DebitCredit, 
                'Outlet Payment - ' || pc.name as Description, 
                'VOUCHER' as RowGroup, 
                6 as RowOrder1, 
                row_number() over()+45 as RowOrder2 
            From pos_session s left join pos_order po on po.session_id = s.id
                left join pos_order_line pol on pol.order_id = po.id
                left join product_product pp on pp.id = pol.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                left join product_category pc on pc.id = pt.categ_id
                left join pos_category posc on posc.id = pt.pos_categ_id
            where s.working_date = '{pos_date}' and
                po.company_id = {company_id} and
                -- s.state = 'closed' and
                po.state not in ('draft', 'cancel')
                and po.employee_id is null and po.department_id is null 
                and posc.id is null
            group by s.working_date, pc.name
            union
            select ps.working_date as TrxDate, 
                aj.name as ItemType, 
                0 as SubdepartmentId, 
                sum(coalesce(abcl.amount,0)) as Amount, 
                -1 as DebitCredit, 
                case 
                    when aj.is_bank_edc_credit_card=true then 'Outlet Payment - ' || aj.name 
                    else 'Outlet Payment'
                end as Description, 
                case 
                    when aj.type = 'cash' then 'CASH' 
                    when aj.is_bank_edc_credit_card then 'CREDIT CARD' 
                    when aj.is_city_ledger then 'CITY LEDGER'
                    when aj.is_point then 'POINT'
                    when aj.is_advance_payment then 'BANQUET DEPOSIT'
                end as RowGroup, 
                case 
                    when aj.type = 'cash' then 2
                    when aj.is_bank_edc_credit_card then 3
                    when aj.is_city_ledger then 4
                    when aj.is_point then 5
                    when aj.is_advance_payment then 5
                end as RowOrder1, 
                row_number() over(partition by aj.name)+4 as RowOrder2
            from pos_session ps
                left join account_bank_statement abc on abc.pos_session_id = ps.id
                left join account_bank_statement_line abcl on abcl.statement_id = abc.id
                left join account_journal aj on aj.id = abc.journal_id
            where ps.working_date = '{pos_date}' 
                and aj.company_id = {company_id}
                and not aj.is_officer_check and not aj.is_department_expense
                and not aj.is_charge_room
                and abcl.amount != 0
            group by ps.working_date, aj.name, aj."type", aj.is_bank_edc_credit_card, aj.is_city_ledger
                , aj.is_point, aj.is_advance_payment
            order by roworder1, roworder2
            """.format(company_id=company_id, pos_date=pos_date)

        # self.env.cr.execute(query, tuple(params))
        http.request.env.cr.execute(query)
        pos_trx_summary = http.request.env.cr.dictfetchall()

        return pos_trx_summary


def get_pos_data_open_session(company_id, working_date):
    # get pos transaction data for Daily Card Report
    query = """SELECT a.config_id, a.name, a.user_id, d.login as user_name, a.working_date, a.state, b.name as pos, c.name as company_name
        from pos_session a 
        left join pos_config b on a.config_id = b.id 
        left join res_company c on b.company_id = c.id
        left join res_users d on a.user_id = d.id
        where a.working_date='{working_date}' and a.state != 'closed' and b.company_id='{company_id}'
        """.format(company_id=company_id, working_date=working_date)

    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    pos_session_summary = http.request.env.cr.dictfetchall()

    return pos_session_summary
    # # if not data:
    # move = self.env['pos.order'].with_context(force_company=company_id)._create_account_move(
    #     session.start_at,
    #     session.name,
    #     int(journal_id),
    #     company_id
    # )
    # orm_pos_session = http.request.env['pos.session']
    # pos_sessions = orm_pos_session.sudo().search_read([])
    # _logger.debug(pos_sessions)
    # session: stop_at, state = close
    # cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
    #
    # orm_pos_session = registry.get('pos.session')
    # session_ids = orm_pos_session.search(cr, SUPERUSER_ID, [], context=context)


def get_pos_data_pos_payment_details(company_id, start_working_date, end_working_date, pms_payment_type):
    # get pos transaction data for Night Audit Report
    query = """select cashier.name as cashier, coalesce(order_in.name,po.name) as order_ref, sum(absl.amount) as amount,
        session_in.shift_id as shift_id, hs.description as shift,
        po.pos_reference as receipt_ref, kit.id as card_id, kit.name as card_type, 
        absl.card_number as card_number, po.customer_id as company_id, rp.name as company_name, kgvc.is_external,
        po.my_value_id as SIP_card_number, po.my_value_name as member_name, ps.working_date,
        absl.voucher_no as voucher_no, kgvc.voucher_pms_id as voucher_pms_id, kgvc.name as voucher_name
        from pos_session ps
        left join account_bank_statement abs on abs.pos_session_id = ps.id
        left join account_bank_statement_line absl on absl.statement_id = abs.id
        left join pos_order po on po.id = absl.pos_statement_id
        left join pos_order order_in on order_in.id = po.apply_id
        left join pos_session session_in on session_in.id = coalesce(order_in.session_id,po.session_id)
        left join kg_issuer_type kit on kit.id = absl.issuer_type_id
        left join account_journal ac on ac.id = absl.journal_id
        left join kg_voucher kgvc on kgvc.id = absl.voucher_id
        left join journal_payment_group jpg on jpg.id = ac.journal_payment_group_id
        left join res_partner rp on rp.id = po.customer_id
        left join hr_shift hs on hs.id = session_in.shift_id
        left join res_users ru on ru.id = po.user_id
        left join res_partner cashier on cashier.id = ru.partner_id    
        where po.company_id = {company_id} and
        (ps.working_date >= '{start_working_date}' and ps.working_date <= '{end_working_date}') and
        jpg.pms_payment_type ='{pms_payment_type}'
        group by cashier.name , coalesce(order_in.name,po.name), hs.description,
        po.pos_reference, kit.id, kit.name,session_in.shift_id,
        absl.card_number, po.customer_id, rp.name, po.my_value_id, po.my_value_name, absl.voucher_no, 
        kgvc.voucher_pms_id, kgvc.name, ps.working_date, kgvc.is_external
        having sum(absl.amount) !=0
        order by po.pos_reference
        """.format(company_id=company_id, start_working_date=start_working_date,
                   end_working_date=end_working_date, pms_payment_type=pms_payment_type)
    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    pos_payment_details = http.request.env.cr.dictfetchall()

    return pos_payment_details


def get_pos_data_voucher_statistic(company_id, working_date):
    # get pos transaction data for voucher statistic Report
    selected_year = datetime.strptime(working_date, '%Y-%m-%d').strftime('%Y')
    start_date = "{year}{start_date}".format(year=selected_year, start_date='/01/01')
    working_month = datetime.strptime(working_date, '%Y-%m-%d').strftime('%m')
    query = """select kgvc.name, kgvc.voucher_pms_id, kgvc.is_external,
            count(case when abs.date = '{working_date}' then absl.id end) as dtd_qty,
            sum(case when abs.date = '{working_date}' then absl.amount else 0 end) as dtd_amount,
            count(case when date_part('month', abs.date) = '{working_month}' and abs.date <= '{working_date}' then absl.id end) as mtd_qty,
            sum(case when date_part('month', abs.date) = '{working_month}' and abs.date <= '{working_date}' then absl.amount else 0 end) as mtd_amount,   
            count(absl.id) as ytd_qty,
            sum(absl.amount) as ytd_amount
            from account_journal aj
            left join account_bank_statement abs on abs.journal_id = aj.id 
            left join account_bank_statement_line absl on abs.id = absl.statement_id
            left join kg_voucher kgvc on kgvc.id = absl.voucher_id
            where aj.is_voucher is true  and aj.company_id = {company_id}
            and abs.date between '{start_date}' and '{working_date}'
            and absl.amount is not null
            group by kgvc.name, kgvc.voucher_pms_id, kgvc.is_external
        """.format(company_id=company_id, start_date=start_date,
                   working_month=working_month, working_date=working_date)

    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    pos_voucher_statistic = http.request.env.cr.dictfetchall()

    return pos_voucher_statistic


def get_history_point_transaction(company_id, start_date, end_date, point_type):
    # get pos transaction data for history point transaction Report

    query_order = """order by order_ref desc"""
    query_earn = """select cashier.name as cashier, po.name as order_ref, ps.shift_id as shift_id, hs.description as shift_name,
                po.pos_reference as receipt_ref, po.my_value_id as SIP_card_number,
                po.my_value_name as member_name, ps.working_date as working_date,
                po.my_value_earn_amount as amount, po.my_value_earn_point as earning_point, 
                (my_value_earn_amount * 0.02) as commision, 'Earning' as point_type from pos_session ps
                    left join pos_order po on po.session_id = ps.id
                    left join hr_shift hs on hs.id = ps.shift_id
                    left join pos_category pc on pc.id = po.outlet_id
                    left join res_users ru on ru.id = po.user_id
                    left join res_partner cashier on cashier.id = ru.partner_id
                where (ps.working_date >= '{start_date}' and ps.working_date <= '{end_date}') and 
                    po.company_id = {company_id} and po.my_value_earn_amount != 0 and po.my_value_earn_point != 0
                """
    union = """ union """
    query_redeem = """select cashier.name as cashier, po.name as order_ref, ps.shift_id as shift_id, hs.description as shift_name,
                        po.pos_reference as receipt_ref, po.my_value_id as SIP_card_number,
                        po.my_value_name as member_name, ps.working_date as working_date,
                        absl.amount as amount, 0 as earning_point,0 as commision, 'Redeem' as point_type from pos_session ps
                            left join pos_order po on po.session_id = ps.id
                            left join account_bank_statement_line absl on po.id = absl.pos_statement_id
                            left join account_journal aj on aj.id = absl.journal_id
                            left join hr_shift hs on hs.id = ps.shift_id
                            left join pos_category pc on pc.id = po.outlet_id
                            left join res_users ru on ru.id = po.user_id
                            left join res_partner cashier on cashier.id = ru.partner_id
                        where (ps.working_date >= '{start_date}' and ps.working_date <= '{end_date}') and
                        po.company_id = {company_id} and aj.is_point is true   
                        """

    if point_type == 'earn':
        query = (query_earn+query_order).format(company_id=company_id, start_date=start_date,
                                                end_date=end_date)

    elif point_type == 'redeem':
        query = (query_redeem+query_order).format(company_id=company_id, start_date=start_date,
                                                  end_date=end_date)
    else:
        query = (query_earn+union+query_redeem+query_order).format(company_id=company_id, start_date=start_date,
                                                                   end_date=end_date)

    # self.env.cr.execute(query, tuple(params))
    http.request.env.cr.execute(query)
    history_point_transaction = http.request.env.cr.dictfetchall()

    return history_point_transaction
