# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
import base64
import json
import requests

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_pac = fields.Selection(selection_add=[('it_admin', 'IT Admin')])
    saldo_timbres =  fields.Float(string=_('Saldo de timbres'), readonly=True)
    saldo_alarma =  fields.Float(string=_('Alarma timbres'), default=10)
    correo_alarma =  fields.Char(string=_('Correo de alarma'))

    @api.model
    def get_saldo_by_cron2(self):
        companies = self.search([('l10n_mx_edi_pac', '!=', 'it_admin')])
        for company in companies:
            company.get_saldo()
#            if company.saldo_timbres < company.saldo_alarma and company.correo_alarma:
#                email_template = self.env.ref("nomina_cfdi_ee.email_template_alarma_de_saldo",False)
#                if not email_template:return
#                emails = company.correo_alarma.split(",")
#                for email in emails:
#                    email = email.strip()
#                    if email:
#                        email_template.send_mail(company.id, force_send=True,email_values={'email_to':email})
        return True

    def get_saldo2(self):
        values = {
                 'rfc': self.vat,
                 'api_key': 'multifactura',
                 'modo_prueba': False,
                 }
        url=''
        url = '%s' % ('http://facturacion.itadmin.com.mx/api/saldo')
        try:
            response = requests.post(url,auth=None,verify=False, data=json.dumps(values),headers={"Content-type": "application/json"})
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
