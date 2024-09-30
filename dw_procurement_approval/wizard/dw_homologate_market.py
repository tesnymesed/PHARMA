from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from odoo import Command


class DwAttributeMarket(models.TransientModel):
    _name = "procurement.approval.market.wizard"
    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1, readonly=1)
    approval_id = fields.Many2one("procurement.supplier.approval", check_company=True,
                                  domain='[("supplier_id","=", supplier_id),("state","in", ["approval"]),("market_ids","not in", market_id)]',
                                  string="Approval")
    line_id = fields.Many2one("procurement.market.dw.line", string="Line Market")
    market_id = fields.Many2one("procurement.market.dw", string="Market", related="line_id.market_id")
    line_approved = fields.Boolean(default=False)
    product_id = fields.Many2one(
        'product.product',
        check_company=True, required=1,
        domain=['|', '|', ('need_approval', '=', True),
                ('categ_id.need_approval', '=', True),
                ('product_tmpl_id.need_approval', '=', True), ('purchase_ok', '=', True)], readonly=1
    )
    quantity = fields.Float('Needed Quantity', readonly=1)
    company_id = fields.Many2one(
        'res.company', related="line_id.company_id",
    )

    def _prepare_approval_values(self, market_id, product_id, supplier_id, qty):
        return {
            'name': 'New',
            'market_ids': [Command.link(market_id.id)],
            'product_id': product_id.id,
            'supplier_id': supplier_id.id,
            'qty': qty,
        }

    def action_confirm_create_approval(self):

        line_id = self.line_id
        market_id = line_id.market_id
        approval_data = self._prepare_approval_values(market_id, self.product_id, self.supplier_id,
                                                          self.quantity)
        if approval_data:
            approval = self.env['procurement.supplier.approval'].create(approval_data)
            self.line_approved = True
            self.approval_id = approval.id
            return approval

    def action_link_approval_to_market(self):

        line_id = self.line_id
        market_id = line_id.market_id
        approval_id = self.approval_id
        if not approval_id:
            raise ValidationError(
                _('You must choose an approval to go further')
            )
        approval_id.write({"market_ids":[Command.link(market_id.id)]})
        self.line_approved = True

    def action_link_all_approval_to_market(self):
        records_to_link = self.filtered(lambda line: line.approval_id)
        for record in records_to_link:
            record.action_link_approval_to_market()

    def action_confirm_all_create_approval(self):
        records_to_create = self.filtered(lambda line: not line.approval_id)
        for record in records_to_create:
            record.action_confirm_create_approval()

    def action_confirm(self):
        self.line_id.market_id.write({"state": "approval_consultation"})

