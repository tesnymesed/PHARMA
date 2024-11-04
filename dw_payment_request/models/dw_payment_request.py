# -*- coding:utf-8 -*-

from odoo import fields, models, api, _
import datetime


class DwPaymentRequest(models.Model):
    _name = "dw.payment.request"

    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: _('New') )
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
        group_expand='_expand_states'
    )
    user_id = fields.Many2one('res.users', 'Agent', default=lambda self: self.env.user , required="true")
    confirmed_by_id = fields.Many2one('res.users', 'Confirmed by')
    request_date = fields.Date(
        string="Request date",
        default=fields.Date.context_today,
        required=True,
    )
    date_limit = fields.Date(
        string="deadline",
    )
    validation_date = fields.Date(
        string="Validation date ",
    )
    payment_request_type = fields.Many2one('account.payment.method.line', string="payment method",required=True)
    date = fields.Date("Date")
    reject_motif_id = fields.Many2one('dw.reject.reason', string='Reject reason')
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',

    )
    dw_account_move_id = fields.Many2one('account.move', string='Account move')

    amount_in_text = fields.Char(string="Amount in Text",)
    payment_reference = fields.Char(string="payment reference")
    Payment_order = fields.Char(string="Payment order")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    montant = fields.Monetary(string="Amount", currency_field="currency_id", required=True)

    request_type_id = fields.Many2many('payment.request.type',string='Request Type',required=True)

    @api.depends('dw_account_move_id.amount_total')  
    #must be improved
    def _compute_amount_in_text(self):
        for rec in self:
            currency = self.env['res.currency'].search([('name', '=', rec.dw_account_move_id.currency_id.name)],
                                                       limit=1)
            ctx = self._context.copy()
            ctx['lang'] = 'fr_FR'

            amount_net = rec.dw_account_move_id.amount_total

            rec.amount_in_text = currency.with_context(ctx).amount_to_text(amount_net)

    def action_confirm(self):
            today=fields.Date.today()
            user_id=fields.Date.today()
            self.write({
                'state': 'confirm',
                'confirmed_by_id': user_id,
                'validation_date': today,
            })

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
