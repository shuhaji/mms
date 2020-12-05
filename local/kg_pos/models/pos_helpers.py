# -*- coding: utf-8 -*-

from odoo import api, models
import requests
import json
import urllib.parse

from odoo.exceptions import UserError
from requests.exceptions import ConnectionError
import datetime


class POSHelpers(models.AbstractModel):
    _name = 'pos.helpers'

    @api.model
    def get_api_data(self):
        #url = 'https://dev.api.hospitality.mykg.id'
        url = self.env['ir.config_parameter'].get_param('pms.api_url')
        # url = self.env['ir.config_parameter'].search([('key', '=', 'pms.api_url')], limit = 1)
        # user_login_id = self.env['ir.config_parameter'].search([('key', '=', 'pms.login_id')], limit = 1)
        user_password = self.env['ir.config_parameter'].get_param('pms.password')
        user_id = self.env['ir.config_parameter'].get_param('pms.user_id')
        # current_user = self.env['res.users'].browse(self._uid)
        current_company = self.env.user.company_id

        if not url or not user_id or not user_password:
            raise UserError("System Parameters for pms.api_url or pms.user_id or pms.password not exists")

        hotel_id = current_company.hotel_id if (current_company and current_company.hotel_id) else None
        if not hotel_id:
            raise UserError("PMS Hotel ID in master Company is required")

        return {
            'url': url,
            # 'user_login_id': user_login_id,
            'user_id': user_id,
            'user_password': user_password,
            'current_company': current_company,
            'hotel_id': hotel_id
        }
    
    @api.model
    def get_token(self, base_url, user_id, user_password, hotel_id):
       #url = 'https://dev.api.hospitality.mykg.id'

        url = urllib.parse.urljoin(base_url, '/api/login')
        
        data = {
            "hotelId": "0",  # for login, send 0 in hotel id, hotel_id,
            "userId": user_id,  # "ODOO_USER",
            "userPassword": user_password,  # "12345"
        }

        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, data=json.dumps(data), headers=headers)
            if response.status_code in (200, 201):
                return response.json().get('access_token')
            else:
                raise UserError("Failed to get token from PMS API"
                                "Response status code = " + str(response.status_code) +
                                ". Response: " + str(response.content))
        except ConnectionError as ex:
            raise UserError("Failed to get token from PMS API. Check your connection.")

    @api.model
    def get_pms_tax_online(self, working_date):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')
        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/get-tax-onine-data'

        url = urllib.parse.urljoin(base_url, '/api/GetLocalTax')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'HotelId': hotel_id,
            'UserId': user_id,
            'TrxDate': working_date
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get Tax Online data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))

    @api.model
    def get_folio(self, room_number):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')
        try:
            pms_token = self.get_token(
                base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
            )

            # url = 'https://kg-pms-api-dev.azurewebsites.net/api/GetInHouseFolio'
            url = urllib.parse.urljoin(base_url, '/api/GetInHouseFolio')

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer %s' % pms_token
            }

            data = {
                'HotelId': hotel_id,
                'UserId': user_id,
                'RoomNo': room_number
            }
            response = requests.post(url, data=json.dumps(data), headers=headers)
            # return response.json()
            if response.status_code == 200:
                return response.json()
            # elif response.status_code != 200:
            else:
                response = JsonResponseError(
                    code=33303,
                    message="Failed to get data Room Number ! Response Status Code = " +
                        str(response.status_code) +
                        ", content: " + str(response.content),
                    http_status_code=303
                ).to_dict()
                return response
        except (ConnectionError, UserError):
            response = JsonResponseError(
                    code=33412,
                    message="Failed to get Room Number. Check your connection.",
                    http_status_code=412,
                    ).to_dict()
            return response

    @api.model
    def post_payment(self, order):
        # Charge to Room Payment
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        hotel_id = api_config.get('hotel_id')

        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        original_amount = order.amount_total - order.amount_tax

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/PointOfSales'
        url = urllib.parse.urljoin(base_url, '/api/PointOfSales')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        amount_service_uat = 0.0
        amount_tax_uat = 0.0
         
        for tax in order.pos_tax_ids:
            if ('Service' or 'service') in tax.name:
                amount_service_uat = tax.pos_order_tax_amount or 0.0

            elif ('Tax' or 'tax') in tax.name:
                amount_tax_uat = tax.pos_order_tax_amount or 0.0

        data = {
            'HotelId': hotel_id,
            'UserId': user_id,
            'SubdepartmentId': 1,  # should use value from sub dept order.department_id.id??
            'FolioId': order.folio_id,
            'Pax': order.customer_count,
            'OrderReference': order.name,
            'OriginalAmount': original_amount,
            'DiscountPct': 0,
            'DiscountAmount': 0,
            'Amount': original_amount,
            'ServiceAmount': amount_service_uat,
            'TaxAmount': amount_tax_uat,
            'NetAmount': order.amount_total,
            'MemberId': '',
            'MemberReference': '',
            'AppSource': 'ODOO',
            'Remark': order.config_id.name,
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            json_response = response.json()
            pos_id = json_response.get("PosId") if json_response else None
        return pos_id

    @api.model
    def post_adv_payment(self, advance_payments):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        hotel_id = api_config.get('hotel_id')

        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/DepositBalance'
        url = urllib.parse.urljoin(base_url, '/api/DepositBalance')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        # balance = sum(payment.residual for payment in adv_payment.advance_payment_ids)
        # data = {
        #     'HotelId': hotel_id,  # should use value from company later on
        #     'DepositId': 119,
        #     'UserId': user_id,
        #     'BalanceAmount': balance,
        # }
        # post_request = requests.post(url, data=json.dumps(data), headers=headers)
        response = list()
        for adv_deposit in advance_payments:
            if adv_deposit.communication and adv_deposit.communication.isdigit():
                pms_adv_deposit_id = int(adv_deposit.communication)
                data = {
                    'HotelId': hotel_id,  # should use value from company later on
                    'DepositId': pms_adv_deposit_id,
                    'UserId': user_id,
                    'BalanceAmount': adv_deposit.residual,
                }
                post_request = requests.post(url, data=json.dumps(data), headers=headers)
                response.append(post_request)
        return response

    def get_my_value_config(self, is_point=True):
        if is_point:
            url = self.env['ir.config_parameter'].get_param('myvalue.api_url_point')
            key = "myvalue.api_url_point"
        else:
            url = self.env['ir.config_parameter'].get_param('myvalue.api_url_membership')
            key = "myvalue.api_url_membership"
        api_token = self.env['ir.config_parameter'].get_param('myvalue.api_token')
        response = None
        if not url or not api_token:
            response = JsonResponseError(
                code=33412,
                message="Setting [System Parameter] with key: " + key +
                        " and myvalue.api_token is not defined correctly. Please contact admin.",
                http_status_code=412  # precondition failed
            ).to_dict()
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % api_token
        }

        return url, headers, response

    @api.model
    def get_myvalue_customer(self, my_value_id):
        # pms_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6IjMiLCJuYmYiOjE1MjEwOTY2MjUsImV4cCI6MTgzNjcxNTgyNSwiaWF0IjoxNTIxMDk2NjI1LCJpc3MiOiJtbXMiLCJhdWQiOiIzIn0.FegXMlh_g243OxuhEDpE7dBtCtqeHx0Cs49oW26zsJM'
        # pms_token = url = self.env['ir.config_parameter'].get_param('pms.get_token')
        base_url, headers, err_response = self.get_my_value_config(is_point=False)
        if err_response:
            return err_response

        # url = 'https://staging-membership.myvalue.id/api/members? cardnumber=&memberno=%s&email=&mobilephone= &showpoint=1&excludemembertype=3' % myvalue_id
        # url = 'https://staging-membership.myvalue.id/api/members?memberno=%s' % myvalue_id
        # base_url = "https://staging-membership.myvalue.id"
        url = urllib.parse.urljoin(base_url, '/api/members?memberno=%s&valueid=%s' % (my_value_id, my_value_id))

        response = requests.get(url, headers=headers)
        return self.process_my_value_response(response)

    def process_my_value_response(self, response):
        if response.status_code == 401:
            return self.return_401_response()
        elif response.status_code != 200:
            return JsonResponseError(
                code=33303,
                message="Failed to get data from MyValue api! Response Status Code = " +
                        str(response.status_code) +
                        ", content: " + str(response.content),
                http_status_code=303  # see other
            ).to_dict()
        return response.json()

    @staticmethod
    def return_401_response():
        return JsonResponseError(
            code=33401,
            message="Unauthorized! MyValue Token is invalid (check Setting [System Parameter] with key: "
                    "myvalue.api_token). Please contact admin.",
            http_status_code=412  # precondition failed
        ).to_dict()

    @api.model
    def get_myvalue_customer_with_point(self, data):
        if data:
            my_value_id = data.get('ValueID', '')

            base_url, headers, err_response = self.get_my_value_config()
            if err_response:
                return err_response

            url = urllib.parse.urljoin(base_url, '/api/point?valueid=%s' % my_value_id)
            # url = 'https://staging-point.myvalue.id/api/point?valueid=%s&memberno=&email=&cardnumber=' % my_value_id

            response = requests.get(url, headers=headers)

            return self.process_my_value_response(response)
    
    @api.model
    def send_earn_points(self, my_value_points_data):
        my_value_id = my_value_points_data.get('my_value_data', False).get('ValueID', '')
        id_outlet = my_value_points_data.get('my_value_outlet_id', '')
        my_value_points_used = my_value_points_data.get('my_value_points_used', 0.0)
        # ReferenceNo : order_name = order.pos_reference + '/S/' + order.session_id
        order_name = my_value_points_data.get('order_name', '')
        transaction_date = my_value_points_data.get('transaction_date', '')
        total_earn = my_value_points_data.get('amount_untaxed', 0.0) - my_value_points_used

        if total_earn > 0 and id_outlet:
            base_url, headers, err_response = self.get_my_value_config()
            if err_response:
                return err_response

            url = urllib.parse.urljoin(base_url, '/api/point/transaction')
            # url = 'https://staging-point.myvalue.id/api/point/transaction'

            data = {
                "MutasiTypeName": "EARNING",
                "Searchby": "KG_ID",
                "Id": my_value_id,
                "IdOutlet": id_outlet,
                # "IdOutlet": "xcsfwdfawf",
                # ReferenceNo : order_name = order.pos_reference + '/S/' + order.session_id
                "ReferenceNo": order_name,
                "CreatedDate": transaction_date,
                "Amount": total_earn,
                "J_Point": 0,
                "ExchangeRate": 0,
                "AmountPoint": 0,
            }

            response = requests.post(url, data=json.dumps(data), headers=headers)
            response_code = response.status_code

            """
                response my value: 
                {
                    "Message": "Earning Transaction Success",
                    "Data": {
                        "Point": 50000.0
                    }
                }
            """
            total_earn_point = 0
            if response.status_code in [200, 201]:
                data = response.json()
                total_earn_point = data.get('Data').get('Point', 0) if data.get('Data') else 0

            response_value = {
                'response': response.json(),
                'code': response_code,
                'total_earn': total_earn,
                'total_earn_point': total_earn_point
            }
        else:
            # earn <= 0.. do nothing
            response_value = {
                'response': {
                    "Message": "POS Config Outlet Id Empty/Not Set!" if not id_outlet else "Earn Amount == 0"
                },
                # if outlet id not set in POS Config, set error status code = 422 (= error from my value)
                'code': 422 if not id_outlet else 200,
                'total_earn': total_earn,
                'total_earn_point': 0
            }

        return response_value
    
    @api.model
    def send_redeem_points(self, my_value_points_data):
        my_value_id = my_value_points_data.get('my_value_data', False).get('ValueID', '')
        id_outlet = my_value_points_data.get('my_value_outlet_id', '')
        my_value_points_used = my_value_points_data.get('my_value_points_used', 0.0)
        order_name = my_value_points_data.get('order_name', '')
        transaction_date = my_value_points_data.get('transaction_date', '')

        base_url, headers, err_response = self.get_my_value_config()
        if err_response:
            return err_response

        url = urllib.parse.urljoin(base_url, '/api/point/transaction')
        # url = 'https://staging-point.myvalue.id/api/point/transaction'

        data = {  
            "MutasiTypeName": "REDEEM",
            "Searchby": "KG_ID",
            "Id": my_value_id,
            "IdOutlet": id_outlet,
            # "IdOutlet": "xcsfwdfawf",
            "ReferenceNo": order_name,
            "CreatedDate": transaction_date,
            "Amount": my_value_points_used,
            "J_Point": 0,
            "ExchangeRate": 0,
            "AmountPoint": 0,
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        response_code = response.status_code

        response_value = {
            'response': response.json(),
            'code': response_code,
            'total_redeem': my_value_points_used,
        }

        return response_value

    @api.model
    def send_pos_daily_summary_to_pms_crm(self, working_date=None):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        hotel_id = api_config.get('hotel_id')

        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        url = urllib.parse.urljoin(base_url, '/api/OdooFoodBeverageRevenue')
        # url = 'https://staging-point.myvalue.id/api/point/transaction'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        cr = self.env.cr
        if not working_date:
            working_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d 04:30:00')

        query = """
            SELECT comp.hotel_id, pc.id as SubDepartmentId, 
            SUM(CASE WHEN prodcat.name = 'Food' THEN (l.price_subtotal) 
             ELSE 0 END) AS FoodRevenue,
            SUM(CASE WHEN prodcat.name = 'Beverage' THEN (l.price_subtotal) 
             ELSE 0 END) AS BeverageRevenue,
            SUM(CASE WHEN prodcat.name != 'Food' AND prodcat.name != 'Beverage' THEN (l.price_subtotal) 
             ELSE 0 END) AS OtherRevenue
            FROM pos_session ps LEFT JOIN pos_order o ON ps.id = o.session_id
            LEFT JOIN pos_order_line l ON o.id = l.order_id
            LEFT JOIN product_product e ON l.product_id = e.id
            LEFT JOIN product_template f ON e.product_tmpl_id = f.id
            LEFT JOIN product_category prodcat ON f.categ_id = prodcat.id
            LEFT JOIN pos_category pc ON f.pos_categ_id = pc.id
            LEFT JOIN res_company comp ON comp.id = o.company_id
            WHERE ps.working_date = %s AND            
            o.state != 'draft' AND o.state != 'cancel'	
            AND prodcat.name IN ('Food', 'Beverage', 'Other')
            AND comp.hotel_id IS NOT NULL
            GROUP BY comp.hotel_id, pc.id;
        """

        self._cr.execute(query, [working_date])
        res = cr.dictfetchall()

        for r in res:
            hotel_id = r.get('hotel_id')
            sub_dept_id = r.get('subdepartmentid')
            food_revenue = r.get('foodrevenue')
            beverage_revenue = r.get('beveragerevenue')
            other_revenue = r.get('otherrevenue')

            data = {
                 "HotelId": hotel_id,
                 "UserId": user_id,
                 "TrxDate": working_date,
                 "SubdepartmentId": sub_dept_id,
                 "FoodRevenue": food_revenue,
                 "BeverageRevenue": beverage_revenue,
                 "OtherRevenue": other_revenue
            }

            response = requests.post(url, data=json.dumps(data), headers=headers)
            response_code = response.status_code

            response_value = {
                'response': response.json(),
                'code': response_code,
            }

        # return response_value

    @api.model
    def get_return_charge_to_room(self, order):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')

        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        original_amount = order.amount_total - order.amount_tax

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/PointOfSales'
        url = urllib.parse.urljoin(base_url, '/api/PointOfSales')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        amount_service_uat = 0.0
        amount_tax_uat = 0.0

        for tax in order.pos_tax_ids:
            if ('Service' or 'service') in tax.name:
                amount_service_uat = tax.pos_order_tax_amount or 0.0

            elif ('Tax' or 'tax') in tax.name:
                amount_tax_uat = tax.pos_order_tax_amount or 0.0

        data = {
            'PosId': order.pms_pos_id,
            'HotelId': hotel_id,
            'UserId': user_id,
            'SubdepartmentId': 1,  # should use value from sub dept order.department_id.id??
            'FolioId': order.folio_id,
            'Pax': order.customer_count,
            'OrderReference': order.name,
            'OriginalAmount': original_amount,
            'DiscountPct': 0,
            'DiscountAmount': 0,
            'Amount': original_amount,
            'ServiceAmount': amount_service_uat,
            'TaxAmount': amount_tax_uat,
            'NetAmount': order.amount_total,
            'MemberId': '',
            'MemberReference': '',
            'AppSource': 'ODOO',
            'Remark': order.config_id.name,
        }

        response = requests.delete(url, data=json.dumps(data), headers=headers)
        return response

    @api.model
    def get_outlet_revenue(self, working_date):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')
        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/get-tax-onine-data'

        url = urllib.parse.urljoin(base_url, '/api/OutletRevenue')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': user_id,
            'HotelId': hotel_id,
            'TrxDate': working_date,
            'ReportType': 0
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get Outlet Summary data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))

    @api.model
    def get_guest_info(self, working_date, room_no=""):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')
        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/get-tax-onine-data'

        url = urllib.parse.urljoin(base_url, '/api/GetReservation')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': user_id,
            'HotelId': hotel_id,
            'InHouseDate': working_date,
            'RowFilter': 2,
            'RoomNo': room_no
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get Guest Info data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))

    @api.model
    def get_meal_allocation(self, working_date, reservation_id=0):
        api_config = self.get_api_data()
        base_url = api_config.get('url')
        user_id = api_config.get('user_id')
        password = api_config.get('user_password')
        # current_company = api_config.get('current_company', False) or False
        hotel_id = api_config.get('hotel_id')
        pms_token = self.get_token(
            base_url=base_url, user_id=user_id, user_password=password, hotel_id=hotel_id
        )

        # url = 'https://kg-pms-api-dev.azurewebsites.net/api/get-tax-onine-data'

        url = urllib.parse.urljoin(base_url, '/api/GetMealAllocation')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': user_id,
            'HotelId': hotel_id,
            'TrxDate': working_date,
            'ReservationId': reservation_id
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get Meal Allocation data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))

class JsonResponseError(object):

    def __init__(self, code, message, data="", http_status_code=400):
        self.code = code
        self.message = message
        self.data = data
        self.http_status_code = http_status_code

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "data": self.data,
            }
        }
