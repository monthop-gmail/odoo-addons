from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

ADVISORY_ENGINE = 'deterministic mock classifier (DEV/SIMULATED — advisory only, never consequential)'


class VillageIssue(models.Model):
    _name = 'village.issue'
    _description = 'Resident service request (Fast POC)'
    _order = 'id desc'

    house_id = fields.Many2one('village.house', required=True, index=True, ondelete='cascade')
    title = fields.Char(required=True, help="Resident request in Thai, e.g. ไฟถนนหน้าบ้านดับ")
    description = fields.Text()
    reported_by = fields.Many2one('res.partner')
    state = fields.Selection([
        ('reported', 'Reported'),
        ('advised', 'AI advisory ready (draft)'),
        ('approved', 'Approved by staff — work order created'),
        ('work_order_done', 'Work order done'),
    ], default='reported', index=True)
    advisory_ids = fields.One2many('village.ai.advisory', 'issue_id')
    maintenance_request_id = fields.Many2one('maintenance.request', readonly=True, index=True)


class VillageAiAdvisory(models.Model):
    _name = 'village.ai.advisory'
    _description = 'AI advisory output (DETERMINISTIC MOCK — advisory only, human approval required)'

    issue_id = fields.Many2one('village.issue', required=True, index=True, ondelete='cascade')
    engine = fields.Char(default=ADVISORY_ENGINE, readonly=True)
    category = fields.Selection([
        ('lighting', 'Lighting'), ('plumbing', 'Plumbing'), ('security', 'Security'),
        ('cleaning', 'Cleaning'), ('other', 'Other'),
    ], readonly=True)
    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], readonly=True)
    summary = fields.Text(readonly=True)
    work_order_text = fields.Text(readonly=True, help="Draft text for the maintenance work order (needs staff approval).")
    state = fields.Selection([
        ('draft', 'Draft — awaiting staff'),
        ('approved', 'Approved (human)'),
        ('rejected', 'Rejected (human)'),
    ], default='draft', index=True)
    approved_by = fields.Many2one('res.users', readonly=True)
    approved_at = fields.Datetime(readonly=True)
    maintenance_request_id = fields.Many2one('maintenance.request', readonly=True)

    _RULES = [
        (('ไฟ', 'ดับ', 'หลอด'), 'lighting', 'high'),
        (('น้ำ', 'รั่ว', 'ท่อ'), 'plumbing', 'high'),
        (('รปภ.', 'ขโมย', 'ปลอดภัย', 'กล้อง'), 'security', 'medium'),
        (('ขยะ', 'กวาด', 'สะอาด'), 'cleaning', 'low'),
    ]

    @api.model
    def generate_for_issue(self, issue):
        """Deterministic mock AI output. Advisory ONLY: this never touches approvals,
        work orders, money, or committee decisions — staff review is mandatory."""
        text = f"{issue.title} {issue.description or ''}"
        category, priority = 'other', 'medium'
        for keywords, cat, prio in self._RULES:
            if any(k in text for k in keywords):
                category, priority = cat, prio
                break
        return self.create({
            'issue_id': issue.id,
            'category': category,
            'priority': priority,
            'summary': f"[ADVISORY ONLY / {ADVISORY_ENGINE}] สรุปปัญหา: {issue.title} — จำแนกหมวด '{category}' ความเร่งด่วน '{priority}'",
            'work_order_text': (
                f"[DRAFT — รอเจ้าหน้าที่ตรวจ/แก้ไข/อนุมัติ] สร้างใบสั่งงานซ่อมบำรุง: "
                f"พื้นที่ {issue.house_id.code} หมวด {category} ความสำคัญ {priority} — {issue.title}"),
            'state': 'draft',
        })

    def action_approve(self):
        """Human approval gate. Approval is the ONLY path that creates the work order."""
        import hashlib
        for advisory in self.filtered(lambda a: a.state == 'draft'):
            digest = hashlib.sha256(f"wo|{advisory.issue_id.id}|{advisory.issue_id.title}".encode()).hexdigest()[:8].upper()
            request = self.env['maintenance.request'].create({
                'name': f"[{advisory.issue_id.house_id.code}] {advisory.work_order_text.split('] ', 1)[-1]}",
                'description': f"{advisory.summary}\nคำขอจากผู้อยู่อาศัย: {advisory.issue_id.title}\nอ้างอิงใบอนุมัติ: WO-{digest}",
                'maintenance_type': 'corrective',
            })
            advisory.write({
                'state': 'approved', 'approved_by': self.env.user.id,
                'approved_at': fields.Datetime.now(), 'maintenance_request_id': request.id,
            })
            advisory.issue_id.write({
                'state': 'approved', 'maintenance_request_id': request.id,
            })

    def action_reject(self):
        for advisory in self.filtered(lambda a: a.state == 'draft'):
            advisory.write({'state': 'rejected', 'approved_by': self.env.user.id, 'approved_at': fields.Datetime.now()})

    def approve(self):
        raise UserError(self.env._(
            "AI/mock engine cannot approve its own advisory — staff approval required (human-controlled)."))

    def write(self, vals):
        if {'issue_id', 'engine'} & set(vals):
            raise UserError(self.env._("Advisory identity/engine fields are immutable (POC)."))
        if self.filtered(lambda a: a.state == 'approved') and (
                {'category', 'priority', 'summary', 'work_order_text'} & set(vals)):
            raise ValidationError(self.env._("Approved advisories are frozen (POC)."))
        return super().write(vals)
