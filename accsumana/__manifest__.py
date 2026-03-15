{
    "name": "Accsumana - Thai Accounting Suite",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "summary": "Install all Thai accounting modules in one click",
    "author": "Accsumana",
    "website": "https://sumana.online",
    "license": "LGPL-3",
    "depends": [
        "l10n_th",
        "l10n_th_account_tax",
        "l10n_th_account_tax_report",
        "l10n_th_account_wht_cert_form",
        "l10n_th_amount_to_text",
        "l10n_th_base_sequence",
        "l10n_th_base_utils",
        # "l10n_th_mis_report",  # TODO: รอ mis_builder port ไป 19.0
        "l10n_th_partner",
        "l10n_th_tier_department",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
