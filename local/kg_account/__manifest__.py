# -*- coding: utf-8 -*-
{
    'name': "Kompas Gramedia Account",
    'summary': """Account Costumization for Kompas Gramedia.""",
    'description': """
        This module manages the followings:
            - Account
    """,
    'author': "",
    'website': "",
    'category': 'Account',
    'version': '11.0.0.0.2',
    'depends': [
        'account_payment_advance_mac5',
        'account',
        'account_cancel',
        'account_budget',
        'kg_report_base',
        'kg_web',
        'account_fiscal_year',  # on vendor/account_fiscal_year
    ],
    'data': [
        'kg_report.xml',
        'data/data_journal.xml',
        'data/data_journal.xml',
        'data/data_digits_precision.xml',
        'data/data_journal_payment_group.xml',
        'reports/report_ar_mutation_pdf_view.xml',
        # 'reports/report_payment_list_ap_view.xml',
        'reports/report_trialbalance.xml',
        'reports/report_financial.xml',
        'reports/report_ap_mutation.xml',
        'reports/report_journals_audit_view.xml',
        # 'reports/report_payments.xml',
        # 'reports/report_new_payment_list_ap.xml',
        'security/ir.model.access.csv',
        'security/account_access_rights.xml',
        'views/account.xml',
        'views/account_invoice.xml',
        'views/account_journal.xml',
        'views/account_payment.xml',
        'views/deposit_type.xml',
        'views/discount_type.xml',
        'views/kg_account_journal_bank.xml',
        'views/kg_issuer_type.xml',
        'views/invoice_collecting_report_layout.xml',
        'views/invoice_collecting_report.xml',
        'views/invoice_collecting_receipt_layout.xml',
        'views/invoice_collecting.xml',
        'views/account_invoice_report_inherit.xml',
        'views/account_invoice_report.xml',
        'views/account_invoice_report_layout.xml',
        'views/kg_customer_invoice_report.xml',
        'views/account_move.xml',
        'views/account_aged_partner_balance_report.xml',
        'views/account_partner_ledger_report.xml',
        'views/res_company.xml',
        'views/templates.xml',
        'views/account_filter_rule.xml',
        'views/vendor_bill_account_bank.xml',
        'views/report_general_ledger.xml',
        'views/account_tax.xml',
        'views/account_financial_report.xml',
        'views/kg_acquirer_transaction.xml',
        'views/account_bank_statement.xml',
        'views/kg_journal_payment_group.xml',
        # 'views/kg_vendor_bill.xml',
        'views/account_budget_views.xml',
        # 'wizard/account_report_payment_view.xml',
        'wizard/kg_credit_card_transaction.xml',
        'wizard/account_invoice_refund_view.xml',
        # 'wizard/invoice_collecting_wizard.xml',
        'wizards/ar_mutation_view.xml',
        # 'wizards/payment_list_ap_view.xml',
        'wizards/voucher_payable.xml',
        'wizards/invoice_verification_register.xml',
        'wizards/ap_mutation_view.xml',
        'wizards/account_report_general_ledger_view.xml',
        'wizards/wizard_kg_report_income_statement.xml',
        'wizards/wizard_kg_report_income_outlook.xml',
        'wizards/wizard_kg_report_balance_sheet.xml',
        'wizards/wizard_kg_report_cash_flow.xml',
        'wizards/wizard_kg_report_journal.xml',
        'wizards/wizard_kg_report_journal_bank.xml',
        'wizards/wizard_kg_report_general_ledger.xml',
        # 'wizards/new_payment_list_ap.xml',
        'wizards/wizard_kg_report_aging_credit_acquirer.xml',
        'wizards/wizard_kg_report_aging_invoice.xml',
        'wizards/wizard_kg_report_trial_balance.xml',
        'wizards/wizard_kg_report_ar_mutation.xml',
        'wizards/wizard_kg_report_ap_mutation.xml',
        'wizards/wizard_kg_report_partner_ledger.xml',
        'wizards/wizard_kg_report_aged_partner_balance.xml',
        'wizards/wizard_kg_report_admin_fee.xml',
        'wizards/account_invoice_refund.xml',
        'wizards/account_move_initial_balance_recalculation.xml',
    ],
    'demo': [
    ],
}