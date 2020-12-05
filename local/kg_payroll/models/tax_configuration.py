from odoo import models, fields, api
from datetime import datetime


class TaxConfiguration(models.Model):
    _name = 'hr.kg.payroll.tax.configuration'

    name = fields.Char(help='Tax Setting Name')

    company_id = fields.One2many('res.company', 'tax_config_id',
                                 help="Company Id")
    tax_penalty_percentage = fields.Float('Tax Penalty Percentage (%)',
                                          help='Tax Penalty Percentage')
    position_percentage = fields.Float('Percentage',
                                       help='Percentage for position')
    position_maxvalue = fields.Float('Max Value',
                                     help='Max Value for position')

    ptkp_id = fields.One2many('hr.kg.payroll.tax.ptkp', 'tax_config_id')

    pkp_id = fields.One2many('hr.kg.payroll.tax.pkp', 'tax_config_id')


class TaxConfigurationPTKP(models.Model):
    _name = 'hr.kg.payroll.tax.ptkp'
    _rec_name = 'tax_state'

    tax_state = fields.Char('Tax Status',
                            help='PTKP Tax State')

    description = fields.Char('Description',
                              help='PTKP Description')

    value = fields.Float('PTKP',
                         help='PTKP Value')

    tax_config_id = fields.Many2one('hr.kg.payroll.tax.configuration')


class TaxConfigurationPTKP(models.Model):
    _name = 'hr.kg.payroll.tax.pkp'
    _rec_name = 'description'

    code = fields.Char('Code',
                       help='Tax PKP Code')

    description = fields.Char('Description',
                              help='Description for PKP')

    max_value = fields.Float('Max Value',
                             help='Max Value for PKP')

    percentage = fields.Float('Percentage',
                              help='PKP Percentage')
    is_unlimited = fields.Boolean('Unlimited', help='Declare unlimited value for max value')

    # company_id = fields.One2many('res.company', string='Company', required=True)

    tax_config_id = fields.Many2one('hr.kg.payroll.tax.configuration')
