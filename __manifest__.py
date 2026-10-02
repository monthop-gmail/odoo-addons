{
    'name': 'Village POC (Juristic Person + AI advisory)',
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': 'Fast POC: village juristic person — houses, common fees, Thai issues, AI advisory (human-approved) work orders',
    'description': """
Fast POC (task-9f7a7314, discussion dis-96d41357) — minimal Thai housing-estate vertical slice on stock Odoo 20:
- house/unit + owner + optional resident (synthetic data only)
- common-fee charges with outstanding/paid state (simulated payment, labeled)
- resident Thai-language service request ("ไฟถนนหน้าบ้านดับ")
- AI assistant that classifies/summarizes/suggests priority/drafts work-order text — DETERMINISTIC MOCK, advisory only
- staff review/approval (human-controlled); approval creates a standard maintenance.request work order and advancing it sets close_date
- house-level dashboard fields: outstanding fee count/amount, open issues, work orders
Reuse map: maintenance.request is REUSE (official community module); common-fee billing would be account.move in production — POC uses a light custom model; helpdesk is Enterprise-only (absent from community source) so issue intake is custom here.
POC only: no production migration, real payment gateway, personal resident data, autonomous approvals, or hardening.
""",
    'author': 'monthop-gmail',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_th', 'maintenance'],
    'data': [
        'security/ir.access.csv',
        'views/village_views.xml',
    ],
    'installable': True,
    'application': False,
    'development_status': 'Alpha',
}
