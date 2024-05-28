# -*- coding:utf-8 -*-

from odoo import fields, models, api, _


class DwPaymentRequest(models.Model):
    _name = "dw.payment.request"


    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        store=True,
    group_expand = '_expand_states'
    )
    user_id = fields.Many2one('res.users', 'Agent', default=lambda self: self.env.user)
    confirmed_by_id = fields.Many2one('res.users', 'Confirmed by')
    request_date = fields.Date(
        string="Request date",
        default=fields.Date.context_today,
    )
    date_limit = fields.Date(
        string="deadline",
    )
    validation_date = fields.Date(
        string="Validationd date ",
    )
    payment_request_type = fields.Many2one('account.payment.method.line', string="payment method")
    date = fields.Date("Date")
    reject_motif_id = fields.Many2one('dw.reject.reason', string='Reject reason')
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',

    )
    dw_account_move_id = fields.Many2one('account.move',string='Account move')
    dw_import_forlder_id = fields.Many2one('dw.import.folder',string='Import Folder')
    def action_confirm(self):
        self.write({'state':'confirm'})
    def action_reject(self):

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reason for rejection',
            'res_model': 'dw.reject.reason.wizard',
            'views': [[self.env.ref('dw_payment_request.dw_reject_reason_form').id, 'form']],
            'target': 'new',

            'context': {
                'default_payment_request_id': self.id, 'dialog_size': 'medium',
            }
        }
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    def action_to_draft(self):
        self.write({'state': 'draft'})
    def _expand_states(self, states, domain, order):
        return [key for key, dummy in self._fields['state'].selection]
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('dw.payment.request') or _('New')
        return super().create(vals_list)

