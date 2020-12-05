from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class KGPurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    @api.model
    def _prepare_item(self, line):
        res = super(KGPurchaseRequestLineMakePurchaseOrder, self)._prepare_item(line)
        res['purchase_type'] = line.request_id.purchase_type
        return res

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin, purchase_type):
        if not self.supplier_id:
            raise UserError(
                _('Enter a supplier.'))
        supplier = self.supplier_id
        data = {
            'origin': origin,
            'partner_id': self.supplier_id.id,
            'fiscal_position_id': supplier.property_account_position_id and
            supplier.property_account_position_id.id or False,
            'picking_type_id': picking_type.id,
            'company_id': company.id,
            'group_id': group_id.id,
            'purchase_type': purchase_type.id,
            'from_purchase_request': True
            }
        return data

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        picking_type = False
        company_id = False
        purch_type = []
        for line in self.env['purchase.request.line'].browse(request_line_ids):
            purch_type.append(line.request_id.purchase_type)

            if line.request_id.state != 'approved':
                raise UserError(
                    _('Purchase Request %s is not approved') %
                    line.request_id.name)

            if line.purchase_state == 'done':
                raise UserError(
                    _('The purchase has already been completed.'))

            line_company_id = line.company_id \
                and line.company_id.id or False
            if company_id is not False \
                    and line_company_id != company_id:
                raise UserError(
                    _('You have to select lines '
                      'from the same company.'))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise UserError(
                    _('You have to enter a Picking Type.'))
            if picking_type is not False \
                    and line_picking_type != picking_type:
                raise UserError(
                    _('You have to select lines '
                      'from the same Picking Type.'))
            else:
                picking_type = line_picking_type

        if len(list(set(purch_type))) > 1:
            raise UserError(
                _('You cannot create a single Purchase Order from '
                  'purchase requests that have different Purchase Type.'))

    @api.multi
    def make_purchase_order(self):
        res = []
        purchase_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        pr_line_obj = self.env['purchase.request.line']
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(
                    _('Enter a positive quantity.'))
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.origin,
                    line.request_id.purchase_type)
                purchase = purchase_obj.create(po_data)

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
                po_line.move_dest_ids |= line.move_dest_ids
            else:
                po_line_data = self._prepare_purchase_order_line(purchase,
                                                                 item)
                if item.keep_description:
                    po_line_data['name'] = item.name
                po_line = po_line_obj.create(po_line_data)
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line,
                new_pr_line=new_pr_line)
            po_line.product_qty = new_qty
            po_line._onchange_quantity()
            # The onchange quantity is altering the scheduled date of the PO
            # lines. We do not want that:
            po_line.date_planned = item.line_id.date_required
            res.append(purchase.id)

        return {
            'domain': [('id', 'in', res)],
            'name': _('RFQ'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'context': False,
            'type': 'ir.actions.act_window'
        }