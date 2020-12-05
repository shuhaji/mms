# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

from odoo import api, fields, models, _
from odoo import tools
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
import logging
import string
import random
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)


def _code_generator(size=8, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
	

class VoucherVoucher(models.Model):
	_name = "voucher.voucher"
	_order = 'create_date desc'
	_inherit = 'mail.thread'
	_description = 'Vouchers'

	@api.model
	def get_default_values(self, field=False):
		irDefault = self.env['ir.default'].sudo()
		vals = {}
		if field:
			return irDefault.get('res.config.settings', '%s'%field)
		vals['product_id'] =  irDefault.get('res.config.settings', 'wk_coupon_product_id')
		vals['default_validity'] =  irDefault.get('res.config.settings', 'wk_coupon_validity') or -1
		vals['max_amount'] =  irDefault.get('res.config.settings', 'wk_coupon_max_amount') or 1000
		vals['min_amount'] =  irDefault.get('res.config.settings', 'wk_coupon_min_amount') or 0
		vals['max_expiry_date'] =  irDefault.get('res.config.settings', 'wk_coupon_max_expiry_date') or datetime.now().date()
		vals['default_availability'] =  irDefault.get('res.config.settings', 'wk_coupon_validity') or 1
		vals['default_value'] =  irDefault.get('res.config.settings', 'wk_coupon_value') or 100
		vals['partially_use'] =  irDefault.get('res.config.settings', 'wk_coupon_partially_use') or False
		vals['voucher_usage'] =  irDefault.get('res.config.settings', 'wk_coupon_voucher_usage') or 'both'
		vals['customer_type'] =  irDefault.get('res.config.settings', 'wk_coupon_customer_type') or 'general'
		vals['partial_limit'] =  irDefault.get('res.config.settings', 'wk_coupon_partial_limit') or -1
		vals['use_minumum_cart_value'] =  irDefault.get('res.config.settings', 'wk_coupon_minumum_cart_value_usage') or False
		vals['minimum_cart_amount'] =  irDefault.get('res.config.settings', 'wk_coupon_minimum_cart_amount') or 1000
		vals['wk_coupon_name'] =  irDefault.get('res.config.settings', 'wk_coupon_name') or 1000
		return vals

	name = fields.Char(
		string='Name', 
		size=100, 
		required=True, 
		default=lambda self: self.get_default_values('wk_coupon_name'),
		help="This will be displayed in the order summary, as well as on the invoice.")
	voucher_code = fields.Char(
		string='Code', 
		size=13,
		help="Secret 13 digit code use by customer to redeem this coupon.")
	create_date = fields.Datetime(
		string='Create Date',
		 help="Date on which voucher is created.")
	issue_date = fields.Date(
		string='Applicable From',
		help="Date on which voucher is issued.",
		default=datetime.now().date())
	expiry_date = fields.Date(
		string='Expiry Date',
		help="Date on which voucher is expired.", 
		default=lambda self: self.get_default_values('wk_coupon_max_expiry_date') or datetime.now().date())
	validity = fields.Integer(
		string='Validity(in days)',
		default=lambda self: self.get_default_values('wk_coupon_validity') or 0,
		help="Validity of this Voucher in days")
	total_available = fields.Integer(
		string='Total Available',
		required=True, 
		default=lambda self: self.get_default_values('wk_coupon_availability') or 10,
		help="The cart rule will be applied to the first 'X' customers only.(-1 for unlimited )")
	voucher_value = fields.Float(
		string='Voucher Value', 
		required=True, 
		default=lambda self: self.get_default_values('wk_coupon_value') or 100)
	note = fields.Text(
		string='Description',
		help="This information will be dispayed to the customers oon front end")
	active = fields.Boolean(
		string='Active',
		help="By unchecking the active field you can disable this voucher without deleting it.",default=1)
	user_id = fields.Many2one(
		comodel_name='res.users', 
		string='Created By')
	customer_id = fields.Many2one(
		comodel_name='res.partner', 
		string='Created For', 
		help='Optional: The cart rule will be available to everyone if you leave this field blank.',
		domain=[('customer','=',True)])
	available_each_user = fields.Integer(
		string='Total available for each user',
		help="A customer will only be able to use the cart rule 'X' time(s).",
		default=-1)
	voucher_val_type  = fields.Selection(
		[('percent', '%'),
		('amount', 'Fixed')],
		required=True, 
		default="amount")
	date_of_last_usage =  fields.Date(
		string='Date of last usage',
		help="the dat of the last usage of the coupon.")
	voucher_usage = fields.Selection(
		[('both', 'Both POS & Ecommerce'),
		('ecommerce', 'Ecommerce'),
		('pos', 'Point Of Sale')],
		required=True,
		default=lambda self: self.get_default_values('wk_coupon_voucher_usage') or 'both',
		string="Coupon Used In" ,
		help="Choose where you want to use the coupon pos/ecommerce and odoocore")
	voucher_value_left = fields.Float(
		compute="_get_total_voucher_value_remained", 
		string="Total value left",
		help="the amount of the voucher left")
	customer_type = fields.Selection(
		[('special_customer', 'Specific Customers'),
		('general', 'All Customers')], 
		required=True, 
		default=lambda self: self.get_default_values('wk_coupon_customer_type') or 'general',
		string="Coupon for" ,
		help="On choosing the General the coupon can be applied for all customers, and on choosing the Special Customer the Coupon can be used for a particlar customer and can be partially redeemed.If the customer type is choosen as new Customers the coupon will be appllied for new registered customers.")
	is_partially_redemed = fields.Boolean(
		string='Use Partial Redemption',
		default=lambda self: self.get_default_values('wk_coupon_partially_use'), 
		help="Enable this option partial redemption option.")
	redeemption_limit = fields.Integer(
		string='Max Redemption Limit',
		required=True, 
		default=lambda self: self.get_default_values('wk_coupon_partial_limit') or -1, 
		help="The maximum number of times the coupon can be redeemed. -1 means the coupon can be used any number of times untill the voucher value is Zero.")
	use_minumum_cart_value = fields.Boolean(
		string='Use Cart Amount Validation',
		default=lambda self: self.get_default_values('wk_coupon_minumum_cart_value_usage'), 
		help="Use this option for using this voucher based on the cart amount.")
	minimum_cart_amount = fields.Float(
		string='Minimum Cart Amount',
		default=lambda self: self.get_default_values('wk_coupon_minimum_cart_amount') or 1000,
		help="Apply this coupon only if the cart value is greater than this amount.")
	applied_on = fields.Selection(
		[('all','All Products'),
		('specific','Specific Products')],
		string='Voucher Applied on',
		default="all",
		required=True,
		help="Products on which the voucher is applied")
	product_ids = fields.Many2many(
		'product.template', 
		'voucher_id',
		'product_id', 
		'voucher_product_rel', 
		string='Products',
		help="Add products on which this voucher will be valid")
	display_desc_in_web = fields.Boolean(
		string='Display Description in Website', 
		default=True)
	create_date = fields.Datetime(
		string="Created On")
	_sql_constraints = [
		('voucher_code_uniq', 'unique(voucher_code)', 'Voucher Code Must Be Unique !!!'),
	]

	
	@api.multi
	@api.depends('voucher_value','total_available')
	def _get_total_voucher_value_remained(self):
		for obj in self:
			amount_left = 0
			history_objs = self.env['voucher.history'].search([('voucher_id','=',obj.id)])
			if history_objs:
				for hist_obj in history_objs:
					if obj.customer_type == 'special_customer':
						amount_left += self._get_amout_left_special_customer(hist_obj)
					if obj.customer_type == 'general' and obj.total_available > 0: 
						amount_left = obj.total_available * obj.voucher_value
			obj.voucher_value_left = amount_left
	
	@api.onchange('voucher_usage')
	def onchange_voucher_usage(self):
		domain = {}
		if self.voucher_usage:
			if self.voucher_usage == 'pos':
				domain = {'product_ids':[('available_in_pos', '=', True)]}
			if self.voucher_usage == 'ecommerce':
				domain = {'product_ids':[('available_in_pos', '=', False)]}
		return {'domain':domain}

	def _get_amout_left_special_customer(self, hist_obj):
		amount_left = 0
		credit = 0
		debit = 0
		if hist_obj.transaction_type == 'credit':
			credit +=  hist_obj.voucher_value
		if hist_obj.transaction_type == 'debit':
			debit += -hist_obj.voucher_value
		amount_left = credit - debit
		return amount_left


	@api.multi
	def send_mail_to_customers(self):
		if self.customer_type == 'special_customer':
			ir_model_data = self.env['ir.model.data']
			template_obj = self.env['mail.template']
			template_id =  ir_model_data.get_object_reference('wk_coupons','mail_template_voucher_voucher')[1]
			template_obj = self.env['mail.template'].browse(template_id)
			values = {}
			values['email_to'] = self.customer_id.email
			res = template_obj.send_mail(self.id, True ,'',values)
			if res:
				wizard_id = self.env['wizard.message'].create({'text':'Email has been sent successfully to the selected customer..'}).id
				return { 'name':_("Summary"),
						'view_mode': 'form',
						'view_id': False,
						'view_type': 'form',
						'res_model': 'wizard.message',
						'res_id': wizard_id,
						'type': 'ir.actions.act_window',
						'nodestroy': True,
						'target': 'new',
						'domain': '[]',
						}
		else:
			raise ValidationError(("Mail can not be sent. No customer selected.."))

	@api.multi
	def unlink(self):
		for record in self:
			history_objs = record.env['voucher.history'].search([('voucher_id','=',record.id)])
			for obj in history_objs:
				obj.unlink()
		return super(VoucherVoucher, self).unlink()


	@api.model
	def create(self, vals):
		history_values = {}
		product_id = self.get_default_values('wk_coupon_product_id')
		if not product_id:
			raise ValidationError("Sorry, Please configure the module before creating any voucher.")
		if vals.get('total_available') == 0:
			raise  ValidationError(('Total Availability can`t be 0. Choose -1 for unlimited or greater than 0 !!!'))
		if vals['voucher_value'] < self.get_default_values('wk_coupon_min_amount'):
			raise  ValidationError(('You can`t create voucher below this minimum amount (%s) !!!')%self.get_default_values('wk_coupon_min_amount'))
		if vals['voucher_value'] > self.get_default_values('wk_coupon_max_amount'):
			raise  ValidationError(('You can`t create voucher greater than this maximum amount (%s) !!!')%self.get_default_values('wk_coupon_max_amount'))
		if vals.get('voucher_value') <= 0:
			raise  ValidationError(('Voucher Value cannot be <= 0.'))
		vals['user_id']= self._uid
		if not vals.get('voucher_code'):
			vals['voucher_code'] = self._generate_code()
		else:
			vals['voucher_code'] = vals.get('voucher_code').strip()
			if vals['voucher_code'] == '':
				raise  ValidationError(('Code can not contain empty spaces'))
		vals['voucher_code'] = self._check_code(vals['voucher_code'])
		max_expiry_date = vals.get('expiry_date')
		if vals.get('validity') > 0:
			exp_date = (datetime.strptime(vals.get('issue_date'),'%Y-%m-%d').date() + timedelta(days=vals.get('validity')))
			vals['expiry_date'] = exp_date
			if max_expiry_date and  vals.get('expiry_date') < datetime.strptime(str(max_expiry_date),'%Y-%m-%d').date():
				vals['expiry_date'] = max_expiry_date
		diff = -1
		if vals.get('expiry_date'):
			diff = (datetime.strptime(str(vals.get('expiry_date')),'%Y-%m-%d').date() - datetime.strptime(vals.get('issue_date'),'%Y-%m-%d').date()).days
		if int(diff) > vals.get('validity'):
			vals['validity'] = diff
		if str(vals.get('expiry_date')) < vals.get('issue_date'):
			raise  ValidationError(('Applicable date should be less than expiry date.'))
		if not vals.get('expiry_date') and vals.get('validity') < 0:
			vals['expiry_date'] = vals.get('issue_date')
		if vals.get('expiry_date') and datetime.now().date() > datetime.strptime(str(vals['expiry_date']),'%Y-%m-%d').date():
			raise  ValidationError(('Expiry date have been passed already. Please select a correct expiry date..'))
		if vals.get('issue_date') and  datetime.now().date() > datetime.strptime(str(vals.get('issue_date')),'%Y-%m-%d').date():
			raise  ValidationError(('Voucher Applicable date is not correct. Either you can make voucher applicable from today or from a future date.'))
		if vals.get('redeemption_limit') and  vals.get('redeemption_limit')== 0:
			raise  ValidationError(('You cannnot set Reedemption limit To 0'))
		if vals.get('voucher_val_type')== 'percent':
			if vals.get('voucher_value') < 0 or vals.get('voucher_value') >100:
				raise  ValidationError(('The percentage value should be within 0 and 100'))
		res  = super(VoucherVoucher, self).create(vals)
		history_values = {
			'name':vals['name'],
			'create_date':datetime.now(),
			'voucher_value':vals.get('voucher_value'),
			'transaction_type':'credit',
			'channel_used':vals.get('voucher_usage'),
			'voucher_id':res.id
			}
		self.env['voucher.history'].sudo().create(history_values)
		return res

	@api.multi
	def write(self, vals):
		for voucher in self:
			validity = -1
			history_values = {}
			product_id = self.get_default_values('wk_coupon_product_id')
			if not product_id:
				raise ValidationError("Sorry, Please configure the module before creating any voucher.")
			if vals.get('name'):
				history_values['name'] = vals['name']
			if vals.get('validity', False) or vals.get('issue_date',False):
				if not vals.get('issue_date',False):
					vals['issue_date'] = voucher.read(['issue_date'])[0]['issue_date']
				if not vals.get('validity',False):
					validity = voucher.read(['validity'])[0]['validity']
					vals['validity'] = validity
				if not vals.get('expiry_date',False):
					max_expiry_date = voucher.read(['expiry_date'])[0]['expiry_date']
				else:
					max_expiry_date = vals['expiry_date']
				if vals.get('validity') > 0:
					exp_date = (datetime.strptime(vals['issue_date'],'%Y-%m-%d').date()+timedelta(days=vals.get('validity')))
					vals['expiry_date'] = exp_date
					if max_expiry_date and  vals['expiry_date'] < datetime.strptime(str(max_expiry_date),'%Y-%m-%d').date():
						vals['expiry_date'] = max_expiry_date
			if vals.get('validity') == 0:
				raise ValidationError(('Validity can`t be 0. Choose -1 for unlimited or greater than 0 !!!'))
			if vals.get('voucher_value') and vals.get('voucher_value') < self.get_default_values('wk_coupon_min_amount'):
				raise ValidationError(('You can`t create voucher below this minimum amount (%s) !!!')%self.get_default_values('wk_coupon_min_amount'))
			if vals.get('percnet'):
				if vals.get('voucher_value') < 0 or vals.get('voucher_value') > 100:
					raise  ValidationError(('The percentage value should be within 0 and 100'))
			if not vals.get('expiry_date') and validity < 0:
				if vals.get('issue_date'):
					vals['expiry_date'] = vals.get('issue_date')
			if vals.get('expiry_date'):
				if vals.get('issue_date'):
					diff = (datetime.strptime(str(vals['expiry_date']),'%Y-%m-%d').date() - datetime.strptime(vals.get('issue_date'),'%Y-%m-%d').date()).days
				else:
					diff = (datetime.strptime(str(vals['expiry_date']),'%Y-%m-%d').date() - datetime.strptime(voucher.read(['issue_date'])[0]['issue_date'],'%Y-%m-%d').date()).days
				if int(diff) > validity:
					vals['validity'] = diff
			if  vals.get('voucher_value') and vals.get('voucher_value') > self.get_default_values('wk_coupon_max_amount'):
				raise ValidationError(('You can`t create voucher greater than this maximum amount (%s) !!!')%self.get_default_values('wk_coupon_max_amount'))
			if vals.get('redeemption_limit') and  vals['redeemption_limit'] == 0:
				raise  ValidationError(('You cannnot set Reedemption limit To 0'))
			if vals.get('voucher_code'):
				code = vals.get('voucher_code').strip()
				if code == '':
					raise  ValidationError(('Code can not contain empty spaces'))
				else:
					vals['voucher_code'] = voucher._check_write_code(vals['voucher_code'],self.ids)
			if vals.get('voucher_value'):
				history_values['voucher_value'] = vals['voucher_value']
			if vals.get('voucher_usage'):
				history_values['channel_used'] = str(vals['voucher_usage'])
			history_obj = self.env['voucher.history'].sudo().search([('voucher_id','=',self.id),('transaction_type','=','credit')])
			if history_obj:
				history_obj.sudo().write(history_values)
		return super(VoucherVoucher, self).write(vals)

	@api.multi
	def _generate_code(self):
		while True:
			code = _code_generator()
			check = self.search_count([('voucher_code','=',code),('active','in',[True,False])])
			if not check:
				break
		return code

	@api.multi
	def _check_code(self, code):
		exists = self.search_count([('voucher_code','=',code),('active','in',[True,False])])
		if exists:
			raise ValidationError(("Coupon code already exist !!!"))
		return code

	@api.multi
	def _check_write_code(self, code, code_id):
		exists = self.search([('voucher_code','=',code),('active','in',[True,False])])
		if exists:
			if len(exists) == 1 and exists[0].id == code_id:
				return code
			else:
				raise UserError(("Coupon code already exist !!!"))
		return code

	@api.multi
	def _get_voucher_obj_by_code(self, secret_code,refrence):
		self_obj = False
		if refrence and refrence == 'ecommerce':
			self_obj = self.search([('voucher_code','=',secret_code),('active','in',[True,False]),('voucher_usage','in', ['both','ecommerce'])])
		if refrence and refrence == 'pos':
			self_obj = self.search([('voucher_code','=',secret_code),('active','in',[True,False]),('voucher_usage','in', ['both','pos'])])
		return self_obj 
	@api.model
	def _get_default_voucher_values(self):
		irDefault = self.env['ir.default'].sudo()
		res = {}
		return res

	@api.multi
	def _validate_n_get_value(self, secret_code, wk_order_total, product_ids, refrence=False, partner_id=False):
		result={}
		result['status']=False
		defaults = self.get_default_values()
		self_obj = self._get_voucher_obj_by_code(secret_code, refrence)
		if not self_obj:
			result['type']		= _('ERROR')
			result['message']	= _('Voucher doesn`t exist !!!')
			return result
		if not self_obj.active:
			result['type']		= _('ERROR')
			result['message']	= _('Voucher has been de-avtivated !!!')
			return result
		amount_left = 0
		used_vouchers = 0
		voucher_value = self_obj.voucher_value
		total_prod_voucher_price = 0
		used_vouchers = self.env['voucher.history'].sudo().search([('voucher_id','=',self_obj.id),('transaction_type','=','debit')])
		if self_obj.customer_type == 'general' and self_obj.total_available == 0:
			result['type']		= _('ERROR')
			result['message']	= _('Total Availability of this Voucher is 0. You can`t redeem this voucher anymore !!!')
			return result
		if self_obj.customer_type == 'general' and self_obj.total_available > 0 or self_obj.total_available==-1:
			if len(used_vouchers) >= self_obj.available_each_user and self_obj.available_each_user != -1:
				result['type']		= _('ERROR')
				result['message']	= _('Total Availability of this Voucher is 0. You can`t redeem this voucher anymore !!!')
				return result
		if datetime.now().date() < datetime.strptime(self_obj.issue_date,'%Y-%m-%d').date():
			result['type']		= _('ERROR')
			result['message']	= _('Voucher does not exist.')
			return result
		if datetime.strptime(self_obj.expiry_date,'%Y-%m-%d').date() < datetime.now().date():
			result['type']		= _('ERROR')
			result['message']	= _('This Voucher has been expired on (%s) !!!')%self_obj.expiry_date
			return result
		if self_obj.applied_on == 'specific':
			templ_ids = []
			prd_prices = []
			for prod_id in product_ids:
				prod = self.env['product.product'].browse(prod_id)
				templ_id = prod.product_tmpl_id.id
				templ_ids.append(templ_id)
				if templ_id in self_obj.product_ids.ids:
					prd_prices.append(prod.lst_price)
			if prd_prices:
				total_prod_voucher_price += sum(prd_prices)
			contains = set(templ_ids) & set(self_obj.product_ids.ids)
			if not contains:
				result['type']		= _('ERROR')
				result['message']	= _('This voucher is not applicable on the selected products.')
				return result
		if self_obj.use_minumum_cart_value and wk_order_total and wk_order_total < self_obj.minimum_cart_amount:
			result['type']		= _('ERROR')
			result['message']	= _('In order to use this voucher your total order should be equal or greater than %s')%self_obj.minimum_cart_amount
			return result
		if self_obj.customer_type == 'special_customer':
			if self_obj.customer_id.id != partner_id:
				result['type']		= _('ERROR')
				result['message']	= _('Voucher doesn`t exist !!!')
				return result
			if self_obj.is_partially_redemed and self_obj.redeemption_limit != -1:
				if used_vouchers and  len(used_vouchers) >= self_obj.redeemption_limit:
					result['type']		= _('ERROR')
					result['message']	= _('Voucher has been Redeemed to its maximum limit.')
					return result
			history_objs  = self.env['voucher.history'].search([('voucher_id','=',self_obj.id)])
			amount_left = 0
			for hist_obj in history_objs:
				amount_left += self_obj._get_amout_left_special_customer(hist_obj)
			if amount_left <= 0.0:
				result['type']		= _('ERROR')
				result['message']	= _('Total Availability of this Voucher is 0. You can`t redeem this voucher anymore !!!')
				return result
			else:
				voucher_value = amount_left
		result = defaults
		result['status'] = True
		result['type']  =_('SUCCESS')
		result['value'] = voucher_value
		result['coupon_id'] = self_obj.id
		result['coupon_name'] = self_obj.name
		result['total_available'] = self_obj.total_available
		result['voucher_val_type'] = self_obj.voucher_val_type
		result['customer_type'] = self_obj.customer_type
		result['redeemption_limit'] = self_obj.redeemption_limit
		result['applied_on'] = self_obj.applied_on
		result['product_ids'] = self_obj.product_ids.ids
		result['total_prod_voucher_price'] = total_prod_voucher_price
		unit = ''
		if self_obj.voucher_val_type == 'percent':
			unit = 'percent'
		else:
			unit = 'amount'
		result['message']  =_('Validated successfully. Using this voucher you can make discount of %s %s.')%(voucher_value,unit)
		return result

	@api.model
	def validate_voucher(self, secret_code, wk_order_total, products_list ,refrence=False, partner_id=False):
		result = self._validate_n_get_value(secret_code, wk_order_total, products_list, refrence, partner_id)
		return result

	@api.model
	def redeem_voucher_create_histoy(self, voucher_name=False, voucher_id=False, amount=False, order_id=False, order_line_id=False, refrence=False, parter_id=False):
		result = {}
		status = False
		hist_values = {}
		history_obj = False
		if voucher_name and voucher_id and refrence and amount:
			if amount > 0:
				amount = -amount
			hist_values = {
					'name':voucher_name,
					'voucher_id':voucher_id,
					'voucher_value':amount,
					'channel_used':refrence,
					'transaction_type':'debit',
				}
			if parter_id:
				hist_values['user_id'] = parter_id
			if refrence == 'ecommerce':
				hist_values['sale_order_line_id'] = order_line_id
				hist_values['order_id'] = order_id
				history_obj = self.env['voucher.history'].sudo().create(hist_values)
				result['history_id'] = history_obj.id
			voucher_obj  = self.env['voucher.voucher'].sudo().browse(voucher_id)
			status = True
			voucher_obj  = self.browse(voucher_id)
			if refrence != 'pos' and voucher_obj.customer_type == 'general':
				if voucher_obj.total_available > 0:
					voucher_obj.sudo().write({'total_available':voucher_obj.total_available - 1,'date_of_last_usage':datetime.now().date()})
			result['status'] = status
		return result

	@api.model
	def return_voucher(self, coupon_id, line_id, refrence=False, history_id=False):
		voucher_obj = self.browse(coupon_id)
		if voucher_obj.customer_type == 'general' and voucher_obj.total_available >= 0:
			if voucher_obj.total_available != -1:
				voucher_obj.sudo().write({'total_available':voucher_obj.total_available + 1})
		if voucher_obj.customer_type == 'special_customer':
			if refrence ==  'ecommerce':
				history_obj = self.env['voucher.history'].search([('sale_order_line_id','=',line_id)])
				history_obj.unlink()
		return True