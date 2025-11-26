# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError
import base64
import json
import requests

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_pac = fields.Selection(selection_add=[('it_admin', 'IT Admin')])
    saldo_timbres =  fields.Float(string='Saldo de timbres', readonly=True)

    @api.model
    def get_saldo_by_cron2(self):
        companies = self.search([('l10n_mx_edi_pac', '!=', 'it_admin')])
        for company in companies:
            company.get_saldo()
        return True

    def get_saldo2(self):
        values = {
                 'rfc': self.vat,
                 'api_key': 'multifactura',
                 'modo_prueba': False,
                 }
        url=''
        url = '%s' % ('https://facturacion.itadmin.com.mx/api/saldo')
        try:
            response = requests.post(url,auth=None, data=json.dumps(values),headers={"Content-type": "application/json"})
            json_response = response.json()
        except Exception as e:
            print(e)
            json_response = {}
    
        if not json_response:
            return
        
        estado_factura = json_response['estado_saldo']
        if estado_factura == 'problemas_saldo':
            raise UserError(_(json_response['problemas_message']))
        if json_response.get('saldo'):
            xml_saldo = base64.b64decode(json_response['saldo'])
        values2 = {
                    'saldo_timbres': xml_saldo
                  }
        self.update(values2)

    def button_dummy2(self):
        self.get_saldo2()
        return True
