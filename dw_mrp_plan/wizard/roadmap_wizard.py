from odoo import fields, models, api


class RoadmapWizard(models.TransientModel):
    _name = 'roadmap.wizard'

    plan_line_id = fields.Many2one(
        'product.mrp.plan'
    )
    lot_id = fields.Many2one(
        'stock.lot', domain=" [('product_id', '=', product_id)]"

    )
    product_id = fields.Many2one(
        'product.product',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
    )
    bom_id = fields.Many2one(
        'mrp.bom',
        'BoM',
    )
    bom_quantity = fields.Float()

    def action_validate(self):
        datas = self.plan_line_id._prepare_datas_to_roadmap()
        res = self.env['mrp.roadmap'].create(datas)
        res.lot_ids = self.lot_id
        res.quantity_per_lot = self.bom_quantity
        self.plan_line_id.write({
            'roadmap_id': res.id,
            'roadmap_done': True
        })
        return True
