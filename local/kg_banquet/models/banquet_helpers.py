# -*- coding: utf-8 -*-

from odoo import api, models
import requests
import json
import urllib.parse

from odoo.exceptions import UserError
from requests.exceptions import ConnectionError
import datetime


class BanquetHelpers(models.AbstractModel):
    _name = 'banquet.helpers'

    @api.model
    def get_api_data(self):
        # url = 'https://dev.api.hospitality.mykg.id'
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
        # url = 'https://dev.api.hospitality.mykg.id'

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

    @staticmethod
    def return_401_response():
        return JsonResponseError(
            code=33401,
            message="Unauthorized! MyValue Token is invalid (check Setting [System Parameter] with key: "
                    "myvalue.api_token). Please contact admin.",
            http_status_code=412  # precondition failed
        ).to_dict()

    @api.model
    def get_guest_info(self, name, email, phone):
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

        url = urllib.parse.urljoin(base_url, '/api/GetGuestProfileRowPage')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': 'user',
            'HotelId': hotel_id,
            'GuestName': name,
            'EmailAddress': email,
            'MobilePhone': phone
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
    def get_group_info(self):
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

        url = urllib.parse.urljoin(base_url, '/api/getGroup')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': user_id,
            'HotelId': hotel_id
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get Group Info data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))

    @api.model
    def get_room_rate_info(self, rate_type, room_type, person, arrival_date):
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

        url = urllib.parse.urljoin(base_url, '/api/AvailableRoomRate')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': 'admin38',
            'HotelId': 38,
            'CompanyId': 19925,
            'RateType': rate_type,
            'TypeId': room_type,
            'Person': person,
            'ArrivalDate': arrival_date
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Fail" + str(response.content))


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
