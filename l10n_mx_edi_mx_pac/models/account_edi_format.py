import requests
import json

from odoo import models,_
from odoo.exceptions import UserError, Warning
import logging
_logger = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_it_admin_credentials(self, move):
        if move.company_id.l10n_mx_edi_pac_test_env:
            return {
                'sign_url': 'http://facturacion.itadmin.com.mx/api/invoice',
                'cancel_url': 'http://facturacion.itadmin.com.mx/api/refund',
            }
        else:
            return {
                'sign_url': 'http://facturacion.itadmin.com.mx/api/invoice',
                'cancel_url': 'http://facturacion.itadmin.com.mx/api/refund',
            }

    def _l10n_mx_edi_it_admin_sign(self, move, credentials, cfdi):

        values = {
                'enterprise': {
                     'rfc': move.company_id.vat,
                    # 'folio': move.folio,
                    # 'serie_factura': move.company_id.serie_factura,
                     'modo_prueba': move.company_id.l10n_mx_edi_pac_test_env,
                     'xml': cfdi.decode("utf-8"),
                    }
                 }
        try:
            response = requests.post(credentials['sign_url'],auth=None,verify=False, data=json.dumps(values),headers={"Content-type": "application/json"})
        except Exception as e:
            error = str(e)
            if "Name or service not known" in error or "Failed to establish a new connection" in error:
                raise UserError("Servidor fuera de servicio, favor de intentar mas tarde")
            else:
                raise UserError(error)

        if "Whoops, looks like something went wrong." in response.text:
             raise Warning("Error en el proceso de timbrado, espere un minuto y vuelva a intentar timbrar nuevamente. \nSi el error aparece varias veces reportarlo con la persona de sistemas.")

        json_response = response.json()

        estado_factura = json_response['estado_factura']
        if estado_factura == 'problemas_factura':
            raise UserError(_(json_response['problemas_message']))

        # Receive and stroe XML invoice
        if json_response.get('factura_xml'):
            return {
                'cfdi_signed': json_response.get('factura_xml').encode('UTF-8'),
                'cfdi_encoding': 'base64',
            }

    def _l10n_mx_edi_it_admin_cancel(self, move, credentials, cfdi):
        uuid_replace = move.l10n_mx_edi_cancel_invoice_id.l10n_mx_edi_cfdi_uuid

        certificates = move.company_id.l10n_mx_edi_certificate_ids
        certificate = certificates.sudo().get_valid_certificate()

        values = {
                  'rfc': move.company_id.vat,
                  'api_key': 'na', # move.company_id.proveedor_timbrado,
                  'uuid': move.l10n_mx_edi_cfdi_uuid,
                  'folio': 'na', #move.folio,
                  'serie_factura': 'na', #move.company_id.serie_factura,
                  'modo_prueba': move.company_id.l10n_mx_edi_pac_test_env,
                    'certificados': {
                          'archivo_cer': certificate.content.decode('UTF-8'),
                          'archivo_key': certificate.key.decode('UTF-8'),
                          'contrasena': certificate.password,
                    },
                  'xml': cfdi.decode("utf-8"),
                  'motivo': "01" if uuid_replace else "02",
                  'foliosustitucion': uuid_replace,
                  }

        try:
            response = requests.post(credentials['cancel_url'],auth=None,verify=False, data=json.dumps(values),headers={"Content-type": "application/json"})
        except Exception as e:
            error = str(e)
            if "Name or service not known" in error or "Failed to establish a new connection" in error:
                raise Warning("Servidor fuera de servicio, favor de intentar mas tarde")
            else:
                raise Warning(error)

        json_response = response.json()

        if json_response['estado_factura'] == 'problemas_factura':
            raise UserError(_(json_response['problemas_message']))
        elif json_response['estado_factura'] == 'solicitud_cancelar':
            raise Warning(_(json_response['problemas_message']))
        elif json_response.get('factura_xml', False):
            return {'success': True}

    def _l10n_mx_edi_it_admin_sign_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_it_admin_sign(invoice, credentials, cfdi)

    def _l10n_mx_edi_it_admin_cancel_invoice(self, invoice, credentials, cfdi):
        return self._l10n_mx_edi_it_admin_cancel(invoice, credentials, cfdi)

    def _l10n_mx_edi_it_admin_sign_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_it_admin_sign(move, credentials, cfdi)

    def _l10n_mx_edi_it_admin_cancel_payment(self, move, credentials, cfdi):
        return self._l10n_mx_edi_it_admin_cancel(move, credentials, cfdi)

