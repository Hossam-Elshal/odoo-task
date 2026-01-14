from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_high_discount = fields.Boolean(
        string='Has High Discount',
        compute='_compute_has_high_discount',
        store=True,
    )

    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
    ], string='Approval State', default='not_required', tracking=True)

    @api.depends('order_line.discount')
    def _compute_has_high_discount(self):
        for order in self:
            # Check if any line has discount > 10%
            order.has_high_discount = any(line.discount > 10 for line in order.order_line)
            # Update approval_state
            if order.has_high_discount and order.approval_state != 'approved':
                order.approval_state = 'pending'
            elif not order.has_high_discount:
                order.approval_state = 'not_required'

    @api.constrains('order_line')
    def _check_discount_after_approval(self):
        for order in self:
            if order.approval_state == 'approved':
                for line in order.order_line:
                    if line.discount > 10:
                        raise ValidationError(_(
                            "⚠️You cannot modify discount after approval."
                        ))

    def action_confirm(self):
        for order in self:
            if order.approval_state == 'pending':
                raise UserError(_(
                    "You cannot confirm this order.\n\n"
                    "⚠️ Manager Approval Required!\n"
                    "This order has a discount greater than 10%%."
                ))
        return super(SaleOrder, self).action_confirm()

    # ============================================================================
    # Approve discount - Sales Managers only
    def action_approve_discount(self):
        if self.has_high_discount:
            self.approval_state = 'approved'
            self.message_post(
                body=_('Discount approved by %s') % self.env.user.name,
                subject=_('Discount Approved')
            )
# ============================================================================
