import hashlib

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class ImpactPointWallet(models.Model):
    _name = 'impact.point.wallet'
    _description = 'Impact point wallet (separate from donation money ledger — Fast POC)'

    donor_id = fields.Many2one('res.partner', required=True, index=True, ondelete='restrict')
    entry_ids = fields.One2many('impact.point.entry', 'wallet_id')
    balance = fields.Integer(compute='_compute_balance')

    _donor_uniq = models.Constraint(
        'UNIQUE(donor_id)',
        'One impact-point wallet per donor (POC).',
    )

    @api.depends('entry_ids.points', 'entry_ids.kind')
    def _compute_balance(self):
        for wallet in self:
            wallet.balance = sum(wallet.entry_ids.mapped('signed_points'))

    @api.model
    def ensure_for(self, donor):
        wallet = self.search([('donor_id', '=', donor.id)], limit=1)
        return wallet or self.create({'donor_id': donor.id})

    def action_donate_points(self, points, campaign, ref=None):
        """Point use 1: donate points onward to a recipient campaign (no money involved)."""
        self.ensure_one()
        if points > self.balance:
            raise ValidationError(self.env._(
                "Impact wallet %(wallet)s: balance %(balance)d < donate-out %(points)d — refused (fail-closed).",
                wallet=self.donor_id.display_name, balance=self.balance, points=points))
        return self.env['impact.point.entry'].create({
            'wallet_id': self.id, 'kind': 'donate_out', 'points': points,
            'recipient_campaign_id': campaign.id, 'ref': ref or 'point-donation',
        })

    def action_request_conversion(self, points, partner_label, idempotency_key=None, force_outcome=None):
        """Point use 3: convert/export points to an external partner via the MOCK adapter.

        Idempotent by key: repeating the same key returns the existing conversion without
        a second ledger entry. Points are NOT money — success issues only point entries.
        """
        self.ensure_one()
        if points <= 0:
            raise ValidationError(self.env._("Conversion points must be positive."))
        key = idempotency_key or hashlib.sha256(
            f"{self.id}|{points}|{partner_label}".encode()).hexdigest()[:12].upper()
        existing = self.env['impact.point.conversion'].search([('idempotency_key', '=', key)], limit=1)
        if existing:
            return existing
        if points > self.balance:
            raise ValidationError(self.env._(
                "Impact wallet %(wallet)s: balance %(balance)d < convert %(points)d — refused (fail-closed).",
                wallet=self.donor_id.display_name, balance=self.balance, points=points))
        conversion = self.env['impact.point.conversion'].create({
            'wallet_id': self.id, 'points': points,
            'partner_label': partner_label, 'idempotency_key': key,
        })
        adapter = self.env['impact.point.adapter'].search([], limit=1) or self.env['impact.point.adapter'].create({})
        result = adapter.simulate(points, key, force_outcome=force_outcome)
        if result['outcome'] == 'success':
            conversion.write({'state': 'success', 'external_ref': result['external_ref']})
            conversion.entry_id = self.env['impact.point.entry'].create({
                'wallet_id': self.id, 'kind': 'redeem_out', 'points': points,
                'ref': key, 'conversion_id': conversion.id,
            })
        else:
            conversion.write({'state': 'failed'})
        return conversion

    @api.model
    def ensure_demo_setup(self):
        """Idempotent demo/POC configuration (official PromptPay path + sample registry)."""
        env = self.env
        comp = env.company
        th = env['res.country'].search([('code', '=', 'TH')], limit=1)
        if th:
            comp.partner_id.country_id = th
            comp.partner_id.city = comp.partner_id.city or 'Bangkok'
        comp.currency_id = env.ref('base.THB')
        bank = env['res.partner.bank'].search([
            ('partner_id', '=', comp.partner_id.id),
            ('proxy_type', 'in', ['mobile', 'merchant_tax_id', 'ewallet_id']),
        ], limit=1)
        if not bank:
            # No default number in code: a real-looking mobile would route QR payments to a stranger.
            mobile = (env['ir.config_parameter'].sudo().get_param('donation_poc.promptpay_mobile') or '').strip()
            if not mobile:
                raise UserError(
                    "PromptPay mobile is not configured. Set the system parameter "
                    "'donation_poc.promptpay_mobile' (Settings > Technical > System Parameters) "
                    "to the receiving PromptPay mobile number."
                )
            bank = env['res.partner.bank'].create({
                'partner_id': comp.partner_id.id,
                'account_number': mobile,
                'proxy_type': 'mobile',
                'proxy_value': mobile,
            })
        if not env['impact.point.rule'].search([('active', '=', True)], limit=1):
            env['impact.point.rule'].create({})
        def province(code, name):
            found = env['res.country.state'].search([('country_id.code', '=', 'TH'), ('code', '=', code)], limit=1)
            return found or env['res.country.state'].search(
                [('country_id.code', '=', 'TH'), ('name', '=ilike', name)], limit=1) or env['res.country.state'].create({
                    'country_id': th.id, 'code': code, 'name': name,
                })
        kk = province('42', 'Khon Kaen')
        bkk = province('10', 'Bangkok')
        def campaign(name, recipient, category, province):
            found = env['donation.campaign'].search([('name', '=', name)], limit=1)
            return found or env['donation.campaign'].create({
                'name': name, 'recipient_name': recipient, 'category': category, 'province_id': province.id,
            })
        return {
            'bank': bank,
            'campaign_kk': campaign('Flood-relief fund Khon Kaen (POC)', 'Concept charity — Khon Kaen', 'charity', kk),
            'campaign_bkk': campaign('Children hospital fund Bangkok (POC)', 'Concept hospital — Bangkok', 'hospital', bkk),
        }


class ImpactPointEntry(models.Model):
    _name = 'impact.point.entry'
    _description = 'Impact point ledger entry (append-only — carries NO monetary value)'
    _order = 'id desc'

    wallet_id = fields.Many2one('impact.point.wallet', required=True, index=True, ondelete='cascade')
    kind = fields.Selection([
        ('award', 'Award (from donation)'),
        ('donate_out', 'Donated onward to recipient'),
        ('redeem_out', 'Converted/exported via mock adapter'),
    ], required=True)
    points = fields.Integer(required=True)
    ref = fields.Char()
    source_donation_id = fields.Many2one('donation.entry', index=True, ondelete='set null')
    recipient_campaign_id = fields.Many2one('donation.campaign', index=True, ondelete='set null')
    conversion_id = fields.Many2one('impact.point.conversion', index=True, ondelete='set null')
    signed_points = fields.Integer(compute='_compute_signed_points')

    _points_positive = models.Constraint(
        'CHECK (points > 0)',
        'Point entries must be positive; kind carries the direction.',
    )

    @api.depends('kind', 'points')
    def _compute_signed_points(self):
        for entry in self:
            entry.signed_points = entry.points if entry.kind == 'award' else -entry.points

    def write(self, vals):
        immutable = {'wallet_id', 'kind', 'points', 'source_donation_id', 'recipient_campaign_id', 'conversion_id'}
        if immutable & set(vals):
            raise ValidationError(self.env._(
                "Point ledger is append-only (POC): %s cannot change.", ', '.join(sorted(immutable & set(vals)))))
        return super().write(vals)

    def unlink(self):
        raise ValidationError(self.env._("Point ledger is append-only (POC): entries cannot be deleted."))


class ImpactPointConversion(models.Model):
    _name = 'impact.point.conversion'
    _description = 'Point conversion/export request to external partner (MOCK, idempotent — Fast POC)'
    _order = 'id desc'

    wallet_id = fields.Many2one('impact.point.wallet', required=True, index=True, ondelete='cascade')
    points = fields.Integer(required=True)
    partner_label = fields.Char(required=True, help="External partner concept label, e.g. TruePoint-class (concept only).")
    state = fields.Selection([('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')], default='pending')
    idempotency_key = fields.Char(required=True, index=True)
    external_ref = fields.Char(readonly=True)
    entry_id = fields.Many2one('impact.point.entry', readonly=True)

    _key_uniq = models.Constraint(
        'UNIQUE(idempotency_key)',
        'Idempotency key must be unique (POC conversion adapter contract).',
    )


class ImpactPointAdapter(models.Model):
    _name = 'impact.point.adapter'
    _description = 'External partner conversion adapter (MOCK, deterministic — NOT a real integration)'

    name = fields.Char(default='MOCK TruePoint-class adapter (concept only — no real API)')

    def simulate(self, points, idempotency_key, force_outcome=None):
        """Deterministic mock outcome. force_outcome only exists to demonstrate the
        pending/success/fail simulation in POC demo/tests — never a real provider."""
        self.ensure_one()
        digest = hashlib.sha256(f"{points}|{idempotency_key}".encode()).hexdigest()[:8].upper()
        outcome = force_outcome if force_outcome in ('success', 'failed') else 'success'
        return {'outcome': outcome, 'external_ref': f"MOCK-{digest}" if outcome == 'success' else None}
