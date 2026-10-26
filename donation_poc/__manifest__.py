{
    'name': 'Donation POC (Nationwide Donation Network + Impact Point)',
    'version': '20.0.1.0.0',
    'category': 'Nonprofit',
    'summary': 'Fast POC: donation ledger separate from impact-point ledger, mock conversion adapter',
    'description': """
Fast POC — minimal nationwide donation network vertical slice on stock Odoo 20:
- donor -> campaign/recipient registry (province/category) -> simulated monetary donation -> receipt reference -> point issuance
- donation (money) ledger and impact-point ledger are SEPARATE models; points carry no monetary field and issue no money
- configurable earning rule (points per THB)
- three point uses: donate points onward to a recipient, retain balance, convert/export via a MOCK partner adapter
  (TruePoint-class named as concept only — no real integration claimed)
- append-only ledgers, idempotency keys on conversions, fail-closed balance checks
POC only: no real payments, no tax/legal certification, no KYC/AML, no production hardening.
""",
    'author': 'monthop-gmail',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_th'],
    'data': [
        'security/ir.access.csv',
        'views/donation_views.xml',
    ],
    'installable': True,
    'application': False,
    'development_status': 'Alpha',
}
