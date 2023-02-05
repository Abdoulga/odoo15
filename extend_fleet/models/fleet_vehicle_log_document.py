# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.http import request


class FleetVehicleLogDocument(models.Model):
    _name = 'fleet.vehicle.log.document'
    _description = 'Vehicle Document'

    name = fields.Char("Nom du document",required=True,)
    date_delivrance = fields.Date("Date de délivrance",required=True,)
    date_expiration = fields.Date("Date d’expiration",required=True,)
    active = fields.Boolean(default=True)
    fichier_img = fields.Binary(string="Document",required=True,)
    fichier_fname = fields.Char(string="Fichier document",required=True,)
    document_type_id = fields.Many2one("extend_fleet.document_type", "Type de document",required=True)
    state = fields.Selection(
        [('open', 'En cours de validité'),
         ('expired', 'Expiré'),], 'Etat', default='open', readonly=True,
        help='Choisissez la validité du contrat',
        tracking=True,
        copy=False)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True, help='Vehicule concerned by this log', check_company=True)



    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True, help='Vehicle concerned by this log')
    days_left = fields.Integer(compute='_compute_days_left', string='Alerte Date')

    def action_open(self):
        self.write({'state': 'open'})

    def action_expire(self):
        self.write({'state': 'expired'})

    @api.depends('date_expiration')
    def _compute_days_left(self):
        for record in self:
            if record.date_expiration:
                today = fields.Date.from_string(fields.Date.today())
                renew_date = fields.Date.from_string(record.date_expiration)
                diff_time = (renew_date - today).days
                record.days_left = diff_time if diff_time > 0 else 0
            else:
                record.days_left = -1

    @api.model
    def create(self, values):
        res = super(FleetVehicleLogDocument, self).create(values)
        vehicle = request.env['fleet.vehicle'].search([('id','=',res.vehicle_id.id)])
        if values['document_type_id'] == 1 and res['date_expiration'] > vehicle.ccva_date:
            vehicle.write({'ccva_date':res['date_expiration']})
        elif values['document_type_id'] == 3 and res['date_expiration'] > vehicle.assurance_date:
            vehicle.write({'assurance_date': res['date_expiration']})
        return res

    """"@api.model
    def scheduler_manage_document_expiration(self):
        # This method is called by a cron task
        # It manages the state of a contract, possibly by posting a message on the vehicle concerned and updating its status
        params = self.env['ir.config_parameter'].sudo()
        delay_alert_contract = int(params.get_param('hr_fleet.delay_alert_document', default=30))
        date_today = fields.Date.from_string(fields.Date.today())
        outdated_days = fields.Date.to_string(date_today + relativedelta(days=+delay_alert_contract))
        nearly_expired_documents = self.search([('state', '=', 'open'), ('date_expiration', '<', outdated_days)])

        for document in nearly_expired_documents.filtered(lambda contract: contract.user_id):
            document.activity_schedule(
                'fleet.mail_act_fleet_contract_to_renew', document.expiration_date,
                user_id=document.user_id.id)

        expired_documents = self.search(
            [('state', 'not in', ['expired']), ('date_expiration', '<', fields.Date.today())])
        expired_documents.write({'state': 'expired'})

        now_running_documents = self.search([('state', '=', 'futur'), ('start_date', '<=', fields.Date.today())])
        now_running_documents.write({'state': 'open'})

    def run_scheduler(self):
        self.scheduler_manage_document_expiration()"""

    def action_expire(self):
        self.write({'state': 'expired'})

    def write(self, vals):
        res = super(FleetVehicleLogDocument, self).write(vals)
        if 'date_delivrance' in vals or 'date_expiration' in vals:
            date_today = fields.Date.today()
            running_documents, expired_documents = self.env[self._name], self.env[self._name]
            for document in self.filtered(lambda c: c.date_delivrance and c.state != 'closed'):
                if not document.date_expiration or document.date_delivrance <= date_today < document.date_expiration:
                    running_documents |= document
                else:
                    expired_documents |= document
            running_documents.action_open()
            expired_documents.action_expire()
        if vals.get('expiration_date') or vals.get('user_id'):
            self.activity_reschedule(['fleet.mail_act_fleet_contract_to_renew'], date_deadline=vals.get('expiration_date'), new_user_id=vals.get('user_id'))
        return res