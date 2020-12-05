# -*- coding: utf-8 -*-

from odoo import api, models
import requests
import json
import urllib.parse

from odoo.exceptions import UserError
from requests.exceptions import ConnectionError
import datetime

class PosPms(models.AbstractModel):
    _inherit = 'pos.helpers'

    @api.model
    def get_system_date_from_pms(self):
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

        url = urllib.parse.urljoin(base_url, 'api/SystemConfig')

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % pms_token
        }

        data = {
            'UserId': user_id,
            'HotelId': hotel_id,
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:

            return response.json()
        else:
            # error from pms api, raise + error message and status code
            raise UserError("Failed to get SystemDate/working date data from PMS. "
                            "Response status code = " + str(response.status_code) +
                            ". Response: " + str(response.content))