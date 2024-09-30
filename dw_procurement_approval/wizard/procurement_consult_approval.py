from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProcurementConsultApproval(models.TransientModel):
    _name = 'procurement.consult.approval'
    _description = 'Consult Approval'

    market_id = fields.Many2one("procurement.market.dw", string="Market", check_company=True,
                                domain='[("approval_ids","in", approval_id)]')
    approval_id = fields.Many2one("procurement.supplier.approval", check_company=True)
    company_id = fields.Many2one("res.company", related="approval_id.company_id")

    def _prepare_criteria_line_consultation(self, market_id):
        if not market_id:
            return []
        vals_dict = [
            (0, 0, {'criteria_id': criteria.id}) for criteria in market_id.market_criteria_ids]
        return vals_dict

    def _prepare_consultation(self):
        market_id = self.market_id
        approval_id = self.approval_id
        company_id = self.company_id.id or False
        product_id = approval_id.product_id.id or False
        supplier_id = approval_id.supplier_id.id or False
        return {
            'supplier_id': supplier_id,
            'dw_supplier_nature': approval_id.dw_supplier_nature,
            'product_id': product_id,
            'market_id': market_id.id,
            'approval_id': approval_id.id,
            'qty': approval_id.qty,
            'company_id': company_id,
            "criteria_line_ids": self._prepare_criteria_line_consultation(market_id)
        }

    def action_create_consultation(self):
        self.ensure_one()
        approval_id = self.approval_id
        DwConsultation = self.env['procurement.dw.consultation']
        if approval_id.state != "approval":
            raise ValidationError(
                _('This supplier %(supplier_name)s is not approved for this product %(product_name)s .!',
                  supplier_name=approval_id.supplier_id.name, product_name=approval_id.product_id.name)
            )
        consultation_id = DwConsultation.create(self._prepare_consultation())
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consultation',
            'res_model': 'procurement.dw.consultation',
            'views': [[self.env.ref('dw_procurement.dw_consultation_form_view').id, 'form']],
            'res_id': consultation_id.id,
            'context': {"create": 0},
        }
