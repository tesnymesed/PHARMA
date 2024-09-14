from odoo import fields, models, api, _
from odoo.odoo.fields import Command
from odoo.exceptions import ValidationError


class ProcurementMarketConsultationLine(models.TransientModel):
    _name = "procurement.wizard.line"
    supplier_id = fields.Many2one("res.partner", String="Supplier", domain='[("is_supplier","=", True)]',
                                  check_company=True, required=1, readonly=1)
    consultation_id = fields.Many2one("procurement.dw.consultation",check_company=True,
                                      domain='[("supplier_id","=", supplier_id),("state","in", ["consulted"]),("market_id","=", False)]',
                                      string="Consultation")
    line_id = fields.Many2one("procurement.market.dw.line", string="Line Market")
    market_id = fields.Many2one("procurement.market.dw", string="Market", related="line_id.market_id")
    line_consulted = fields.Boolean(default=False)
    product_id = fields.Many2one(
        'product.product',
        check_company=True, required=1,
        domain=[('purchase_ok', '=', True)], readonly=1
    )
    quantity = fields.Float('Needed Quantity', readonly=1)
    company_id = fields.Many2one(
        'res.company', related="line_id.company_id",
    )

    def _prepare_consultation_values(self, market_id, product_id, supplier_id, qty, criteria_type_ids):
        return {
            'name': 'New',
            'market_id': market_id.id,
            'product_id': product_id.id,
            'supplier_id': supplier_id.id,
            'company_id': market_id.company_id.id,
            'criteria_line_ids': [Command.create({'criteria_id': criteria.id}) for criteria in criteria_type_ids],
            'qty': qty,
        }

    def action_confirm_create_consultation(self):

        # wizard_id = self.line_id
        line_id = self.line_id
        market_id = line_id.market_id
        market_criteria_ids = market_id.market_criteria_ids
        consultation_data = self._prepare_consultation_values(market_id, self.product_id, self.supplier_id,
                                                              self.quantity, market_criteria_ids)
        if consultation_data:
            consultation = self.env['procurement.dw.consultation'].create(consultation_data)
            self.line_consulted = True
            self.consultation_id = consultation.id
            return consultation

    def action_link_consultation_to_market(self):

        # wizard_id = self.line_id
        line_id = self.line_id
        market_id = line_id.market_id
        consultation_id = self.consultation_id
        if not consultation_id:
            raise ValidationError(
                _('You must choose a consultation to go further')
            )
        consultation_id.market_id = market_id.id
        self.line_consulted = True

    def action_link_all_consultation_to_market(self):
        records_to_link = self.filtered(lambda line: line.consultation_id)
        for record in records_to_link:
            record.action_link_consultation_to_market()

    def action_confirm_all_create_consultation(self):
        records_to_create = self.filtered(lambda line: not line.consultation_id)
        for record in records_to_create:
            record.action_confirm_create_consultation()
