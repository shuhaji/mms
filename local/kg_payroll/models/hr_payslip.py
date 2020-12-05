from odoo.fields import Datetime

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    brutto = fields.Float(readonly=True, store=True)
    netto = fields.Float(readonly=True, store=True)
    pph21_amount = fields.Float(readonly=True, store=True)
    pph21_paid = fields.Float(readonly=True, store=True)
    # transfer_request_id_payslip = fields.One2many('bank.transfer.request.payroll', 'transfer_id_payslip', string='Transfer Request ID')
    transfer_request_id_payslips = fields.Many2one('bank.transfer.request.payroll', 'Transfer Request ID')
    nik_npwp_name = fields.Char(compute='get_nik_npwp_name', store=True)
    nik = fields.Char(related='employee_id.employee_id', store=True)
    npwp = fields.Char(related='employee_id.npwp_no', store=True)
    department = fields.Char(related='employee_id.department_id.name', store=True)

    @api.multi
    def get_nik_npwp_name(self):
        for line in self:
            if line.employee_id.employee_id:
                line.nik_npwp_name = "{nik}{strip1}{npwp}{strip2}{name}".format(nik=line.employee_id.employee_id, strip1=' - ',
                                                                        npwp=line.employee_id.npwp_no, strip2=' - ',
                                                                        name=line.employee_id.name)
            else:
                line.nik_npwp_name = ""

    @api.multi
    def action_payslip_cancel(self):
        for payslip in self:
            if payslip.move_id.journal_id.update_posted:
                payslip.move_id.button_cancel()
                payslip.move_id.unlink()
            else:
                payslip.move_id.reverse_moves()
                payslip.move_id = False

        return self.write({'state': 'cancel'})

    @api.multi
    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()

        for payslip in self:
            brutto = payslip.line_ids.filtered(lambda r: r.code == 'GROSSTAX').total
            netto = payslip.line_ids.filtered(lambda r: r.code == 'NET').total
            pph21_amount = payslip.line_ids.filtered(lambda r: r.code == 'PPH21_TOTAL').total
            payslip.write(
                {'brutto': brutto, 'netto': netto, 'pph21_amount': pph21_amount})
            # for line in payslip.line_ids:
            #     rule = self.env['hr.salary.rule'].search([('id', '=', line.salary_rule_id.id)])
            #     line.write(
            #         {'is_taxed': rule.is_taxed,
            #          'type_id': rule.type_id,
            #          'tax_class_id': rule.tax_class_id}
            #     )

        return result

    def _sum_salary_rule_category(self, localdict, category, amount):
        if category.parent_id:
            localdict = self._sum_salary_rule_category(localdict, category.parent_id, amount)
        localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and \
                                                      localdict['categories'].dict[category.code] + amount or amount
        return localdict

    @api.model
    def _get_payslip_lines(self, contract_ids, payslip_id):
        # Override all code, care.. no super, all code must be defined here

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {'list_rules': []}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {
            'categories': categories,
            'rules': rules,
            'payslip': payslips,
            'worked_days': worked_days,
            'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        if len(contracts) == 1 and payslip.struct_id:
            structure_ids = list(set(payslip.struct_id._get_parent_structure().ids))
        else:
            structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            # variables that available in python code
            localdict = dict(baselocaldict, employee=employee, contract=contract, lines=[])

            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule._satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule._compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule

                    # sum the amount for its salary category
                    localdict = self._sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                    current_line = BrowsableObject(
                        employee,
                        dict_object=dict(result_dict[key], rule=rule, total_per_line=tot_rule),
                        env=self.env)
                    localdict['lines'].append(current_line)
                    result_dict[key] = self.finalize_payslip_line(
                        result_dict[key], rule, total_per_line=tot_rule)
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return list(result_dict.values())

    @api.model
    def finalize_payslip_line(self, line_dict, rule, total_per_line):
        # write code to change/manipulate current payslip line
        line_dict.update({
            'is_taxed': rule.is_taxed,
            'type_id': rule.type_id,
            'tax_class_id': rule.tax_class_id
        })
        return line_dict

    @api.model
    def get_amount_by_tax(self, lines, is_taxed=True, tax_class_id='R', type_id='FIXED', category_code=False):
        total = 0
        for line in lines:
            if (line.rule.is_taxed == is_taxed and
                    (not tax_class_id or line.rule.tax_class_id == tax_class_id) and
                    (not type_id or line.rule.type_id == type_id) and
                    (not category_code or line.rule.category_id.code == category_code)):
                total += line.total_per_line
        return total

    @api.multi
    def get_ptkp(self, tax_status_id):
        # payslip.env['hr.payslip'].get_ptkp(employee.tax_status_id)
        ptkp = self.env['hr.kg.payroll.tax.ptkp'].search([
            ('id', '=', tax_status_id.id)
        ])
        return ptkp.value

    @api.multi
    def get_pkp(self, tax_config_id, pkp_value):
        # payslip.env['hr.payslip'].get_pkp(employee.company_id.tax_config_id, pkp1)
        lst = []
        tax_config = self.env['hr.kg.payroll.tax.pkp'].search([
            ('tax_config_id', '=', tax_config_id.id),
        ], order="max_value asc")
        min = 0
        for rec in tax_config:
            max = rec.max_value
            if (pkp_value > min and pkp_value < max) or rec.is_unlimited is True:
                result = (pkp_value - min) * (rec.percentage / 100)
                lst.append(result)
                break
            else:
                result = (max - min) * (rec.percentage / 100)
            lst.append(result)
            min = rec.max_value
        return sum(lst)

    @api.multi
    def get_family(self, fam_status_id):
        # payslip.env['hr.payslip'].get_family(employee.fam_status_id)
        family = self.env['hr.kg.payroll.configuration.family'].search([
            ('id', '=', fam_status_id.id)
        ])
        return family.percentage

    @api.multi
    def get_service_charge(self, payroll_config_id, date):
        # payslip.env['hr.payslip'].get_service_charge(employee.company_id.payroll_config_id, payslip.date_to)

        years = Datetime.from_string(date)
        service_charge = self.env['hr.kg.payroll.configuration.service.charge'].search([
            '&', ('payroll_config_id', '=', payroll_config_id.id),
            ('year', '=', years.year)

        ])
        return service_charge.max_value


class BrowsableObject(object):
    def __init__(self, employee_id, dict_object, env):
        self.employee_id = employee_id
        self.dict = dict_object
        self.env = env

    def __getattr__(self, attr):
        return attr in self.dict and self.dict.__getitem__(attr) or 0.0


class InputLine(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute("""
            SELECT sum(amount) as sum
            FROM hr_payslip as hp, hr_payslip_input as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                            (self.employee_id, from_date, to_date, code))
        return self.env.cr.fetchone()[0] or 0.0


class WorkedDays(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""

    def _sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute("""
            SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
            FROM hr_payslip as hp, hr_payslip_worked_days as pi
            WHERE hp.employee_id = %s AND hp.state = 'done'
            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                            (self.employee_id, from_date, to_date, code))
        return self.env.cr.fetchone()

    def sum(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[0] or 0.0

    def sum_hours(self, code, from_date, to_date=None):
        res = self._sum(code, from_date, to_date)
        return res and res[1] or 0.0


class Payslips(BrowsableObject):
    """a class that will be used into the python code, mainly for usability purposes"""

    def sum(self, code, from_date, to_date=None):
        if to_date is None:
            to_date = fields.Date.today()
        self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                    FROM hr_payslip as hp, hr_payslip_line as pl
                    WHERE hp.employee_id = %s AND hp.state = 'done'
                    AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                            (self.employee_id, from_date, to_date, code))
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    is_taxed = fields.Boolean(string='Taxed')
    tax_class_id = fields.Selection(selection=[('R', 'Regular Income'), ('I', 'Irregular Income')])
    type_id = fields.Selection(selection=[('FIXED', 'Fixed'), ('VAR', 'Var'), ('BPJS', 'BPJS')])
    nik_name = fields.Char(compute='get_nik_name', store=True)
    date_to = fields.Date(related='slip_id.date_to', store=True, string='Periode')
    nik = fields.Char(related='employee_id.employee_id', store=True)
    department = fields.Char(related='employee_id.department_id.name', store=True)

    @api.multi
    def get_nik_name(self):
        for line in self:
            if line.slip_id.employee_id.employee_id:
                line.nik_name = "{nik}{strip}{name}".format(nik=line.slip_id.employee_id.employee_id, strip=' - ',
                                                      name=line.slip_id.employee_id.name)
            else:
                line.nik_name = ""

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    transfer_type = fields.Selection([("combine", "Combine"), ("separate", "Separate")], string='Transfer Type')
    transfer_request_id = fields.Many2one('bank.transfer.request.payroll', string='Transfer Request ID')
