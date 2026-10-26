{
    'name': 'Canteen POC (Cashless vertical slice)',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Fast POC: cashless canteen — PromptPay QR, prepaid wallet, mock external-wallet adapter',
    'description': """
Fast POC (task-43c99f5c, discussion dis-882f5ddd) — minimal cashless canteen vertical slice on stock Odoo 20:
- PromptPay QR top-up via the official l10n_th EMV QR path (no OCA addon, no QR engine reimplementation)
- Prepaid wallet: top-up -> debit -> balance on an append-only ledger
- External wallet adapter path as a clearly labeled MOCK/deterministic adapter (no real provider claimed)
- Shop POS config carries no cash payment method; cash exists only at the top-up point (ledger channel)
POC only: no production hardening, no live merchant credentials, no settlement/compliance.
""",
    'author': 'monthop-gmail',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'l10n_th'],
    'data': [
        'security/ir.access.csv',
        'views/canteen_wallet_views.xml',
    ],
    'installable': True,
    'application': False,
    'development_status': 'Alpha',
}
