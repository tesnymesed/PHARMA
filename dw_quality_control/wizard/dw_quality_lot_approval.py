from odoo import api, fields, models


class DwQualityReload(models.TransientModel):
    _name = "dw.quality.lot.approval"

    check_quality_id = fields.Many2one(
        "quality.check"
    )

    lot_id = fields.Many2one(
        "stock.lot",
    )
    lot_ids = fields.Many2many(
        "stock.lot"
    )
    check_number = fields.Char()
    verdict = fields.Selection([
        ('improper', 'Improper'),
        ('proper', 'Proper')
    ])

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        check_quality_id = self.env['quality.check'].browse(self.env.context['active_id'])
        res["check_quality_id"] = check_quality_id.id
        res["check_number"] = check_quality_id.check_number
        res["verdict"] = check_quality_id.verdict
        res["lot_id"] = check_quality_id.lot_id.id if check_quality_id.lot_id else False
        res["lot_ids"] = check_quality_id.lot_domain
        return res

    def action_lot_approval(self):
        check_quality_id = self.check_quality_id
        check_quality_id.sudo().write({"lot_id": self.lot_id.id,
                                       "check_number": self.check_number,
                                       "verdict": self.verdict})
        check_quality_id.sudo().do_pass_per_quality()
        if check_quality_id.dw_check_ids:
            for quality in check_quality_id.dw_check_ids:
                quality.check_number = check_quality_id.check_number
                quality.verdict = check_quality_id.verdict
                quality.do_pass_per_quality()
