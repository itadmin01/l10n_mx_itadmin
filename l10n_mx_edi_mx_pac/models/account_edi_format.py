import base64
import requests
import json
from collections import defaultdict

from odoo import models,_
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'l10n_mx_edi.document'

    def _get_it_admin_credentials(self, company):
        if company.l10n_mx_edi_pac_test_env:
            return {
                'username': company.l10n_mx_edi_pac_username,
                'sign_url': 'https://facturacion.itadmin.com.mx/api/invoice',
                'cancel_url': 'https://facturacion.itadmin.com.mx/api/refund',
                'modo_prueba': company.l10n_mx_edi_pac_test_env,
            }
        else:
            return {
                'username': company.l10n_mx_edi_pac_username,
                'sign_url': 'https://facturacion.itadmin.com.mx/api/invoice',
                'cancel_url': 'https://facturacion.itadmin.com.mx/api/refund',
                'modo_prueba': company.l10n_mx_edi_pac_test_env,
            }

    def _it_admin_sign(self, credentials, cfdi):

        values = {
                'enterprise': {
                     'rfc': credentials['username'],
                    # 'folio': move.folio,
                    # 'serie_factura': move.company_id.serie_factura,
                     'modo_prueba': credentials['modo_prueba'],
                     'xml': cfdi.decode("utf-8"),
                    }
                 }
        try:
            response = requests.post(credentials['sign_url'],auth=None, data=json.dumps(values),headers={"Content-type": "application/json"})
        except Exception as e:
            error = str(e)
            if "Name or service not known" in error or "Failed to establish a new connection" in error:
                raise UserError("Servidor fuera de servicio, favor de intentar mas tarde")
            else:
                raise UserError(error)

        if "Whoops, looks like something went wrong." in response.text:
             raise UserError("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")

        json_response = response.json()

        estado_factura = json_response['estado_factura']
        if estado_factura == 'problemas_factura':
            raise UserError(_(json_response['problemas_message']))

        # Receive and stroe XML invoice
        if json_response.get('factura_xml'):
            return {
                'cfdi_str': base64.decodebytes(json_response.get('factura_xml').encode('UTF-8')),
            }

    def _it_admin_cancel(self, company, credentials, uuid, cancel_reason, cancel_uuid=None):
        certificates = company['root_company'].l10n_mx_edi_certificate_ids
        certificate = certificates.sudo()._get_valid_certificate()

        values = {
                  'rfc': company['root_company'].vat,
                  'api_key': 'na', # move.company_id.proveedor_timbrado,
                  'uuid': uuid,
                  'folio': 'na', #move.folio,
                  'serie_factura': 'na', #move.company_id.serie_factura,
                  'modo_prueba': company['root_company'].l10n_mx_edi_pac_test_env,
                    'certificados': {
                          'archivo_cer': certificate.content.decode('UTF-8'),
                          'archivo_key': certificate.key.decode('UTF-8'),
                          'contrasena': certificate.password,
                    },
                  'xml': '', #self.attachment_id.raw.decode("utf-8"),
                  'motivo': cancel_reason, #"01" if cancel_uuid else "02",
                  'foliosustitucion': cancel_uuid,
                  }

        try:
            response = requests.post(credentials['cancel_url'],auth=None, data=json.dumps(values),headers={"Content-type": "application/json"})
        except Exception as e:
            error = str(e)
            if "Name or service not known" in error or "Failed to establish a new connection" in error:
                raise UserError("Servidor fuera de servicio, favor de intentar mas tarde")
            else:
                raise UserError(error)

        json_response = response.json()

        if json_response['estado_factura'] == 'problemas_factura':
            raise UserError(_(json_response['problemas_message']))
        elif json_response['estado_factura'] == 'solicitud_cancelar':
            raise UserError(_(json_response['problemas_message']))
        elif json_response.get('factura_xml', False):
            return {'success': True}

#    def _it_admin_sign(self, credentials, cfdi):
#        return self._l10n_mx_edi_it_admin_sign(credentials, cfdi)

#    def _it_admin_cancel_invoice(self, uuid, company, credentials, uuid_replace=None):
#        return self._l10n_mx_edi_it_admin_cancel(uuid, company, credentials, uuid_replace=None)

#    def _l10n_mx_edi_it_admin_sign_payment(self, credentials, cfdi):
#        return self._l10n_mx_edi_it_admin_sign(credentials, cfdi)

#    def _l10n_mx_edi_it_admin_cancel_payment(self, uuid, company, credentials, uuid_replace=None):
#        return self._l10n_mx_edi_it_admin_cancel(uuid, company, credentials, uuid_replace=None)

