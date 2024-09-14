from odoo import fields, models, _, api


class DocumentMarketWizard(models.TransientModel):
    _name = "dw.document.market.wizard"
    cahier_charge_attachment = fields.Binary(string="Specification document")
    cahier_charge_name = fields.Char(string='File name')

    fiche_specification_attachment = fields.Binary(string="Fiches de Spécifications")
    fiche_specification_name = fields.Char(string='File name')

    pv_attribution_attachment = fields.Binary(string="attribution VR")
    pv_attribution_name = fields.Char(string='File name')

    market_id = fields.Many2one("procurement.market.dw", "Market")

    state_market = fields.Selection(
        selection=[
            ('draft', 'Identification of the need'),
            ('approval_consultation', 'Approval/consultation'),
            ('done', 'Assigned'),
            ('cancel', 'Canceled')
        ],
        string="State",
        related="market_id.state",
        store=True,
    )

    def action_confirm(self):
        if self.cahier_charge_attachment and self.cahier_charge_name and self.state_market == 'prospecting':
            pg_recorded = self.env['documents.document'].create({
                'res_model': 'procurement.market.dw',
                'res_id': self.market_id.id,
                'name': self.cahier_charge_name,
                'type': 'binary',

                'datas': self.cahier_charge_attachment,
                'folder_id': self.env.ref('dw_procurement.folder_dw_market').id,
            })
        if self.fiche_specification_attachment and self.fiche_specification_name and self.state_market == 'draft':
            pg_recorded = self.env['documents.document'].create({
                'res_model': 'procurement.market.dw',
                'res_id': self.market_id.id,
                'name': self.fiche_specification_name,
                'type': 'binary',

                'datas': self.fiche_specification_attachment,
                'folder_id': self.env.ref('dw_procurement.folder_dw_market').id,
            })
        if self.pv_attribution_attachment and self.pv_attribution_name and self.state_market == 'homologation_consultation':
            pg_recorded = self.env['documents.document'].create({
                'res_model': 'procurement.market.dw',
                'res_id': self.market_id.id,
                'name': self.pv_attribution_name,
                'type': 'binary',
                'datas': self.pv_attribution_attachment,
                'folder_id': self.env.ref('dw_procurement.folder_dw_market').id,
            })
