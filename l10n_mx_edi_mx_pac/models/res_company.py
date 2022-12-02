# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_pac = fields.Selection(selection_add=[('it_admin', 'IT Admin')])