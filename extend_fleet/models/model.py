# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.addons.account_fleet.models.fleet_vehicle import FleetVehicle
from odoo.http import request


class Categorie(models.Model):
    _name = 'extend_fleet.document_type'

    name = fields.Char('Type de document', required="True")


class Document(models.Model):
    _name = "document"

    name = fields.Char("Nom du document")
    date_delivrance = fields.Date("Date de délivrance")
    date_expiration = fields.Date("Date d’expiration")
    fichier_img = fields.Binary(string="Document")
    fichier_fname = fields.Char(string="Fichier document")
    # vehicle_id = fields.One2many('fleet.vehicle', string="Documents")
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehicle",
        required=True,
        index=True,
        auto_join=True,
        ondelete="cascade",
    )
    document_type_id = fields.Many2one("extend_fleet.document_type", "Type de document")


class VehicleDocument(models.Model):
    _inherit = "fleet.vehicle"

    # document_id = fields.One2many('document','vehicle_id', string="Documents")
    service_cost = fields.Monetary('Coût total des services')
    document_lines = fields.One2many("fleet.vehicle.lines", "vehicle_id", string="Documents")
    document_count = fields.Integer(compute="_compute_count_all", string='Compteur Document')
    log_documents = fields.One2many('fleet.vehicle.log.document', 'vehicle_id', 'Documents')
    assurance_date = fields.Date('Date Exp Assurance',)
    ccva_date = fields.Date('Date Exp CCVA')
    document_renewal_due_soon = fields.Boolean(compute='_compute_document_reminder',
                                               search='_search_document_renewal_due_soon',
                                               string='A un document à renouveler')
    document_renewal_overdue = fields.Boolean(compute='_compute_document_reminder',
                                              search='_search_get_overdue_document_reminder',
                                              string='A un document expiré')
    document_renewal_name = fields.Text(compute='_compute_document_reminder', string='Nom du document à renouveler e plutôt')
    document_renewal_total = fields.Text(compute='_compute_document_reminder',
                                         string='Total document expiré ou expiration moins un')

    """ def _compute_date(self):
        for rec in self:
            docs = request.env["fleet.vehicle.log.document"].search([('vehicle_id', '=', rec.id)])
            for doc in docs:
                if doc.document_type_id and doc.document_type_id ==1:
                    self.ccva_date = doc.date_expiration
                elif doc.document_type_id and doc.document_type_id ==2:
                    self.assurance_date = doc.date_expiration"""



    def _search_document_renewal_due_soon(self, operator, value):
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('hr_fleet.delay_alert_document', default=30))
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        datetime_today = fields.Datetime.from_string(today)
        limit_date = fields.Datetime.to_string(datetime_today + relativedelta(days=+delay_alert_contract))
        res_ids = self.env['fleet.vehicle.log.document'].search([
            ('date_expiration', '>', today),
            ('date_expiration', '<', limit_date),
            ('state', 'in', ['open', 'expired'])
        ]).mapped('id')
        res.append(('id', search_operator, res_ids))
        return res

    def _search_get_overdue_document_reminder(self, operator, value):
        res = []
        assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
        if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
            search_operator = 'in'
        else:
            search_operator = 'not in'
        today = fields.Date.context_today(self)
        res_ids = self.env['fleet.vehicle.log.document'].search([
            ('date_expiration', '!=', False),
            ('date_expiration', '<', today),
            ('state', 'in', ['open', 'expired'])
        ]).mapped('id')
        res.append(('id', search_operator, res_ids))
        return res

    def return_action_to_open_doc(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:

            res = self.env['ir.actions.act_window']._for_xml_id('extend_fleet.%s' % xml_id)
            res.update(
                context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
                domain=[('vehicle_id', '=', self.id)]
            )
            return res
        return False

    @api.depends('log_documents')
    def _compute_document_reminder(self):
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_document = int(params.get_param('hr_fleet.delay_alert_document', default=30))
        for record in self:
            overdue = False
            due_soon = False
            total = 0
            name = ''
            state = ''
            for element in record.log_contracts:
                if element.state in ('open', 'expired') and element.date_expiration:
                    current_date_str = fields.Date.context_today(record)
                    due_time_str = element.expiration_date
                    current_date = fields.Date.from_string(current_date_str)
                    due_time = fields.Date.from_string(due_time_str)
                    diff_time = (due_time - current_date).days
                    if diff_time < 0:
                        overdue = True
                        total += 1
                    if diff_time < delay_alert_document:
                        due_soon = True
                        total += 1
                    if overdue or due_soon:
                        log_contract = self.env['fleet.vehicle.log.contract'].search([
                            ('vehicle_id', '=', record.id),
                            ('state', 'in', ('open', 'expired'))
                        ], limit=1, order='expiration_date asc')
                        if log_contract:
                            # we display only the name of the oldest overdue/due soon contract
                            name = log_contract.name
                            state = log_contract.state

            record.contract_renewal_overdue = overdue
            record.contract_renewal_due_soon = due_soon
            record.contract_renewal_total = total - 1  # we remove 1 from the real total for display purposes
            record.contract_renewal_name = name
            record.contract_state = state

    def toggle_active(self):
        self.env['fleet.vehicle.log.contract'].with_context(active_test=False).search([('vehicle_id', 'in', self.ids)]).toggle_active()
        self.env['fleet.vehicle.log.services'].with_context(active_test=False).search([('vehicle_id', 'in', self.ids)]).toggle_active()
        self.env['fleet.vehicle.log.document'].with_context(active_test=False).search([('vehicle_id', 'in', self.ids)]).toggle_active()
        super(FleetVehicle, self).toggle_active()



    def _compute_count_all(self):
        Odometer = self.env['fleet.vehicle.odometer']
        LogService = self.env['fleet.vehicle.log.services']
        LogContract = self.env['fleet.vehicle.log.contract']
        LogDocument = self.env['fleet.vehicle.log.document']
        for record in self:
            record.service_cost = sum(self.env["fleet.vehicle.log.services"].search([('vehicle_id', '=', record.id)]).mapped('amount'))
            record.odometer_count = Odometer.search_count([('vehicle_id', '=', record.id)])
            record.service_count = LogService.search_count([('vehicle_id', '=', record.id), ('active', '=', record.active)])
            record.contract_count = LogContract.search_count([('vehicle_id', '=', record.id), ('state', '!=', 'closed'), ('active', '=', record.active)])
            record.document_count = LogDocument.search_count([('vehicle_id', '=', record.id),('state', '!=', 'closed'), ('active', '=', record.active)],)
            record.history_count = self.env['fleet.vehicle.assignation.log'].search_count([('vehicle_id', '=', record.id)])




class VehicleDocumentLines(models.Model):
    _name = "fleet.vehicle.lines"

    # document_id = fields.One2many('document','vehicle_id', string="Documents")

    document_id = fields.Many2one("document", string="Documents")
    product_id = fields.Many2one("product.product", string="Produits")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicule")



class ResConfigSettingsDoc(models.TransientModel):
    _inherit = ['res.config.settings']

    delay_alert_document = fields.Integer(string='Delay alert contract outdated', default=30, config_parameter='hr_fleet.delay_alert_document')
