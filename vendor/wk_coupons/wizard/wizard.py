# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

from odoo import api, fields, models, _

class WizardMessage(models.TransientModel):
	_name = "wizard.message"
	
	text = fields.Text('Message')
