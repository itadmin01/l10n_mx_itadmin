import base64
import requests
import json
from collections import defaultdict

from odoo import models, fields, api, _
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

    def _it_admin_cancel(self, cfdi_values, credentials, uuid, cancel_reason, cancel_uuid=None):
        company = cfdi_values['root_company']
        certificate_sudo = cfdi_values['certificate'].sudo()
        cer_pem = base64.b64decode(certificate_sudo.pem_certificate)
        key_pem = base64.b64decode(certificate_sudo.private_key_id.pem_key)

        _logger.info('cfdi_values %s, credentials %s, uuid %s, cancel_reason %s, cancel_uuid %s', cfdi_values, credentials, uuid, cancel_reason, cancel_uuid)
        _logger.info('attachment_id %s ', self.attachment_id.raw.decode())
        values = {
                  'rfc': company.vat,
                  'api_key': 'na', # move.company_id.proveedor_timbrado,
                  'uuid': uuid,
                  'folio': 'na', #move.folio,
                  'serie_factura': 'na', #move.company_id.serie_factura,
                  'modo_prueba': company.l10n_mx_edi_pac_test_env,
                    'certificados': {
                          'archivo_cer': '', #cer_pem,
                          'archivo_key': '', #key_pem,
                          'contrasena': '',
                    },
                  'xml': self.attachment_id.raw.decode(),
                  'motivo': cancel_reason,
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

        _logger.info('response %s', response)

        if "Whoops, looks like something went wrong." in response.text:
            raise UserError("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")

        json_response = response.json()

        if json_response['estado_factura'] == 'problemas_factura':
            raise UserError(_(json_response['problemas_message']))
        elif json_response['estado_factura'] == 'solicitud_cancelar':
            raise UserError(_(json_response['problemas_message']))
        elif json_response.get('factura_xml', False):
            return {'success': True}

    @api.model
    def _get_pac_method_map(self):
        """ Returns a dictionary containing the PAC methods for credentials, sign, or cancel. """
        return {
            'credentials': {
                'finkok': self._get_finkok_credentials,
                'solfact': self._get_solfact_credentials,
                'sw': self._get_sw_credentials,
                'it_admin': self._get_it_admin_credentials,
            },
            'sign': {
                'finkok': self._finkok_sign,
                'solfact': self._solfact_sign,
                'sw': self._sw_sign,
                'it_admin': self._it_admin_sign,
            },
            'cancel': {
                'finkok': self._finkok_cancel,
                'solfact': self._solfact_cancel,
                'sw': self._sw_cancel,
                'it_admin': self._it_admin_cancel,
            },
        }

