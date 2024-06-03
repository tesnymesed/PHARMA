from odoo import api, fields, models

PURCHASE_FREQ = {
    'A': 1,
    'B': 2,
    'C': 3,
    'D': 4,
    'E': 5,
    'F': 6,
    'G': 7,
    'H': 8,
    'I': 9,
    'J': 10,
    'K': 11,
    'L': 12,
    'M': 13,
    'N': 14,
    'O': 15,
    'P': 16,
    'Q': 17,
    'R': 18,
    'S': 19,
    'T': 20,
    'U': 21,
    'V': 22,
    'W': 23,
    'X': 24,
    'Y': 25,
    'Z': 26,
}

NAME_SELECTION = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'),
                  ('I', 'I'),
                  ('J', 'J'), ('K', 'K'), ('L', 'L'), ('M', 'M'), ('N', 'N'), ('O', 'O'), ('P', 'P'), ('Q', 'Q'),
                  ('R', 'R'),
                  ('S', 'S'), ('T', 'T'), ('U', 'U'), ('V', 'V'), ('W', 'W'), ('X', 'X'), ('Y', 'Y'), ('Z', 'Z')]

SELECTION = [('A', 'Once a year'),
             ('B', 'Twice a year'),
             ('C', 'Three times a year'),
             ('D', 'Four times a year'),
             ('E', 'Five times a year'),
             ('F', 'Six times a year'),
             ('G', 'Seven times a year'),
             ('H', 'Eight times a year'),
             ('I', 'Nine times a year'),
             ('J', 'Ten times a year'),
             ('K', 'Eleven times a year'),
             ('L', 'Twelve times a year'),
             ('M', 'Thirteen times a year'),
             ('N', 'Fourteen times a year'),
             ('O', 'Fifteen times a year'),
             ('P', 'Sixteen times a year'),
             ('Q', 'Seventeen times a year'),
             ('R', 'Eighteen times a year'),
             ('S', 'Nineteen times a year'),
             ('T', 'Twenty times a year'),
             ('U', 'Twenty-one times a year'),
             ('V', 'Twenty-two times a year'),
             ('W', 'Twenty-three times a year'),
             ('X', 'Twenty-four times a year'),
             ('Y', 'Twenty-five times a year'),
             ('Z', 'Twenty-six times a year')]


class DWProductPurchaseClass(models.Model):
    _name = 'dw.product.purchase.class'
    _description = "Product Purchase Class"

    name = fields.Selection(NAME_SELECTION, string="Name", required=True, default='A')
    # name = fields.Char(string="Name", required=True, default=_('New'))
    code = fields.Char(string="Code", compute='_compute_code', readonly=False)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company')
    dw_frequency = fields.Integer('Purchase Frequency', compute='_compute_dw_frequency')

    @api.depends('name')
    @api.onchange('name')
    def _compute_dw_frequency(self):
        for record in self:
            record.dw_frequency = PURCHASE_FREQ.get(record.name, 1)

    @api.depends('name')
    @api.onchange('name')
    def _compute_code(self):
        for record in self:
            record.code = record.name


    def get_purchase_interval_days(self):
        """
        Returns the purchase interval in days based on the purchase frequency.
        """
        return 365 // PURCHASE_FREQ.get(self.name, 1)

    def get_purchase_interval_months(self):
        """
        Returns the purchase interval in months based on the purchase frequency.
        """
        return 12 // PURCHASE_FREQ.get(self.name, 1)
