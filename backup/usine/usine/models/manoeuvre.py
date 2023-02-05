# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.http import request


class Manoeuvre(models.Model):
    _name = "usine.manoeuvre"
    _description = "manoeuvre"

    name = fields.Char("Nom")
    lastname = fields.Char("Prénom")
    start_date = fields.Date("Date")
    rate = fields.Float("Taux (CFA)")


class PointageManoeurvre(models.Model):
    _name = "usine.pointage.manoeuvre"
    _description = "Pointage manoeuvre"

    name = fields.Char("Pointage Manoeuvre",default="Pointage Manoeuvre")
    semaine = fields.Char("Semaine")
    year = fields.Char("Année", default=lambda self: self.get_current_year())
    mois = fields.Selection(
        [('janvier', 'Janvier'), ('fevrier', 'Février'), ('mars', 'Mars'),
         ('avril', 'Avril'), ('mai', 'Mai'), ('juin', 'Juin'),
         ('juillet', 'Juillet'), ('aout', 'Août'), ('septembre', 'Septembre'),
         ('octobre', 'Octobre'), ('novembre', 'Novembre'), ('decembre', 'Décembre')]
    )
    mois_year = fields.Char("Mois")
    semaine_du = fields.Date("Du",required=True)
    semaine_au = fields.Date("Au",required=True)
    payment_lines = fields.One2many("usine.payment.manoeuvre.lines", "pointage_id", string="Lignes payment",readonly=True)
    pointage_lines = fields.One2many("usine.pointage.manoeuvre.lines", "pointage_id", string="Lignes pointage")
    amount_total = fields.Float(string='Montal Total', store=True, compute='_amount_all', tracking=5)

    total_package = fields.Integer(string='Total paquets', store=True, compute='_amount_all', tracking=5)
    total_employee = fields.Integer(string='Total employés', store=True, compute='_amount_all', tracking=5)

    def get_current_year(self):
        return datetime.today().year


    def compute_payment(self):
        manoeuvres = self.env['usine.manoeuvre'].search([])
        self.ensure_one()
        self.env['usine.payment.manoeuvre.lines'].sudo().search([]).unlink()
        for manoeuvre in manoeuvres:
            package = pay = 0
            for pointage in self:
                for line in pointage.pointage_lines:
                    if manoeuvre.id == line.employee.id:
                        package += line.package_number
                        pay += line.total
                    vals = {
                        'pointage_id': self.id,
                        'total_payment': pay,
                        'package_number': package,
                        'employee':manoeuvre.id

                    }
                self.env['usine.payment.manoeuvre.lines'].sudo().create(vals)
        return True

    @api.depends('pointage_lines.total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for pointage in self:
            pointage.semaine = "Du "+ str(pointage.semaine_du) + " Au " + str(pointage.semaine_du)
            amount_total = 0.0
            total_package = total_employee = 0
            for line in pointage.pointage_lines:
                amount_total += line.total
                total_package += line.package_number
                total_employee += len(line.employee)
            pointage.update({
                'amount_total': amount_total,
                'total_package': total_package,
                'total_employee': total_employee,
            })


class PointageManoeuvreLines(models.Model):
    _name = "usine.pointage.manoeuvre.lines"

    work_day = fields.Date("Date")
    employee = fields.Many2one('usine.manoeuvre', 'Employé')
    package_number = fields.Integer("Nombre de paquets manipulés")
    rate = fields.Float("Taux")
    type_operation = fields.Many2one("usine.type.operation", "Type opération")
    pointage_id = fields.Many2one("usine.pointage.manoeuvre", string="Pointage")
    total = fields.Float("Total")

    @api.onchange('type_operation')
    def compute_employee_rate(self):
        self.ensure_one()
        for line in self:
            line.rate = line.type_operation.taux

    @api.onchange('package_number', 'rate', 'employee')
    def compute_total(self):
        for emp in self:
            if emp.employee:
                emp.total = emp.type_operation.taux * emp.package_number
                emp.rate = emp.type_operation.taux


class Femme(models.Model):
    _name = "usine.femme"
    _description = "femme"

    name = fields.Char("Nom")
    lastname = fields.Char("Prénom")
    start_date = fields.Date("Date")
    rate = fields.Float("Taux (CFA)")


class PointageFemme(models.Model):
    _name = "usine.pointage.femme"
    _description = "Pointage femmes"

    name = fields.Char("Pointage Femmes", default="Pointage Femmes")
    year = fields.Char("Année", default=lambda self: self.get_current_year())
    mois = fields.Selection(
        [('janvier', 'Janvier'), ('fevrier', 'Février'), ('mars', 'Mars'),
         ('avril', 'Avril'), ('mai', 'Mai'), ('juin', 'Juin'),
         ('juillet', 'Juillet'), ('aout', 'Août'), ('septembre', 'Septembre'),
         ('octobre', 'Octobre'), ('novembre', 'Novembre'), ('decembre', 'Décembre')]
    )
    mois_year = fields.Char("Mois")
    pointage_lines = fields.One2many("usine.pointage.femme.lines", "pointage_id", string="Lignes pointage")
    amount_total = fields.Float(string='Montal Total', store=True, compute='_amount_all', tracking=5)
    payment_lines = fields.One2many("usine.payment.femme.lines", "pointage_id", string="Lignes payment",readonly=True)
    total_package = fields.Integer(string='Total paquets', store=True, compute='_amount_all', tracking=5)
    total_employee = fields.Integer(string='Total employés', store=True, compute='_amount_all', tracking=5)

    def get_current_year(self):
        return datetime.today().year

    def compute_payment(self):
        femmes = self.env['usine.femme'].search([])
        self.ensure_one()
        self.env['usine.payment.femme.lines'].sudo().search([]).unlink()
        for femme in femmes:
            package = pay = 0
            for pointage in self:
                for line in pointage.pointage_lines:
                    if femme.id == line.employee.id:
                        package += line.package_number
                        pay += line.total
                    vals = {
                        'pointage_id': self.id,
                        'total_payment': pay,
                        'package_number': package,
                        'employee':femme.id

                    }
                self.env['usine.payment.femme.lines'].sudo().create(vals)
        return True

    @api.depends('pointage_lines.total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for pointage in self:
            pointage.mois_year = pointage.year + " " + pointage.mois
            amount_total = 0.0
            total_package = total_employee = 0
            for line in pointage.pointage_lines:
                amount_total += line.total
                total_package += line.package_number
                total_employee += len(line.employee)
            pointage.update({
                'amount_total': amount_total,
                'total_package': total_package,
                'total_employee': total_employee,
            })

class PaymentFemmeLines(models.Model):
    _name = "usine.payment.femme.lines"

    employee = fields.Many2one('usine.femme', 'Employé')
    package_number = fields.Integer("Nombre de paquets manipulés")
    pointage_id = fields.Many2one("usine.pointage.femme", string="Pointage")
    total_payment = fields.Float("Total Paiement")

class PaymentManoeuvresLines(models.Model):
    _name = "usine.payment.manoeuvre.lines"

    employee = fields.Many2one('usine.manoeuvre', 'Employé')
    package_number = fields.Integer("Nombre de paquets manipulés")
    pointage_id = fields.Many2one("usine.pointage.manoeuvre", string="Pointage")
    total_payment = fields.Float("Total Paiement")

class PaymentVendeursLines(models.Model):
    _name = "usine.payment.vendeur.lines"

    employee = fields.Many2one('usine.vendeur', 'Employé')
    package_number = fields.Integer("Nombre de paquets manipulés")
    pointage_id = fields.Many2one("usine.pointage.vendeur", string="Pointage")
    total_payment = fields.Float("Total Paiement")




class PointageFemmeLines(models.Model):
    _name = "usine.pointage.femme.lines"

    work_day = fields.Date("Date")
    employee = fields.Many2one('usine.femme', 'Employé')
    type_operation = fields.Many2one("usine.type.operation", "Type opération",
                                     default=1)
    package_number = fields.Integer("Nombre de paquets manipulés")
    rate = fields.Float("Taux")
    pointage_id = fields.Many2one("usine.pointage.femme", string="Pointage")
    total = fields.Float("Total")

    @api.onchange('type_operation')
    def compute_employee_rate(self):
        self.ensure_one()
        for line in self:
            line.rate = line.type_operation.taux

    @api.onchange('package_number', 'type_operation', 'employee')
    def compute_total(self):
        for emp in self:
            if emp.employee:
                emp.total = emp.type_operation.taux * emp.package_number
                emp.rate = emp.type_operation.taux


class Vendeur(models.Model):
    _name = "usine.vendeur"
    _description = "vendeur"

    name = fields.Char("Nom")
    lastname = fields.Char("Prénom")
    start_date = fields.Date("Date")
    commission = fields.Float("Commission (CFA)")


class PointageVendeur(models.Model):
    _name = "usine.pointage.vendeur"
    _description = "Pointage vendeur"

    name = fields.Char("Pointage Vendeur", default="Pointage Vendeurs")
    mois_year = fields.Char("Mois")
    year = fields.Char("Année", default=lambda self: self.get_current_year())
    mois = fields.Selection(
        [('janvier', 'Janvier'), ('fevrier', 'Février'), ('mars', 'Mars'),
         ('avril', 'Avril'), ('mai', 'Mai'), ('juin', 'Juin'),
         ('juillet', 'Juillet'), ('aout', 'Août'), ('septembre', 'Septembre'),
         ('octobre', 'Octobre'), ('novembre', 'Novembre'), ('decembre', 'Décembre')]
    )

    payment_lines = fields.One2many("usine.payment.vendeur.lines", "pointage_id", string="Lignes payment",readonly=True)
    pointage_lines = fields.One2many("usine.pointage.vendeur.lines", "pointage_id", string="Lignes pointage")
    amount_total = fields.Float(string='Montal Total', store=True, compute='_amount_all', tracking=5)

    total_package = fields.Integer(string='Total paquets', store=True, compute='_amount_all', tracking=5)
    total_vendeur = fields.Integer(string='Total vendeurs', store=True, compute='_amount_all', tracking=5)

    def get_current_year(self):
        return datetime.today().year

    @api.depends('pointage_lines.total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for pointage in self:
            pointage.mois_year = pointage.year + " " + pointage.mois
            amount_total = 0.0
            total_package = total_employee = 0
            for line in pointage.pointage_lines:
                amount_total += line.total
                total_package += line.package_number
                total_employee += len(line.employee)
            pointage.update({
                'amount_total': amount_total,
                'total_package': total_package,
                'total_vendeur': total_employee,
            })

    def compute_payment(self):
        vendeurs= self.env['usine.vendeur'].search([])
        self.ensure_one()
        self.env['usine.payment.vendeur.lines'].sudo().search([]).unlink()
        for vendeur in vendeurs:
            package = pay = 0
            for pointage in self:
                for line in pointage.pointage_lines:
                    if vendeur.id == line.employee.id:
                        package += line.package_number
                        pay += line.total
                    vals = {
                        'pointage_id': self.id,
                        'total_payment': pay,
                        'package_number': package,
                        'employee':vendeur.id

                    }
                self.env['usine.payment.vendeur.lines'].sudo().create(vals)
        return True



class PointageVendeurLines(models.Model):
    _name = "usine.pointage.vendeur.lines"

    work_day = fields.Date("Date")
    employee = fields.Many2one('usine.vendeur', 'Employé')
    type_operation = fields.Many2one("usine.type.operation", "Type opération")
    package_number = fields.Integer("Nombre de paquets vendus")
    commission = fields.Float("Commission")
    pointage_id = fields.Many2one("usine.pointage.vendeur", string="Pointage")
    carburant = fields.Float("Carburant")
    total = fields.Float("Total paie")

    @api.onchange('type_operation')
    def compute_employee_commission(self):
        self.ensure_one()
        for line in self:
            line.commission = line.type_operation.taux

    @api.onchange('package_number', 'carburant', 'type_operation', 'commission')
    def compute_total(self):
        for emp in self:
            if emp.type_operation:
                if not emp.type_operation:
                    emp.commission = emp.type_operation.taux
                    emp.commission = emp.type_operation.taux
                emp.total = emp.commission * emp.package_number - emp.carburant


class SuiviMateriaux(models.Model):
    _name = "usine.suivi"

    year = fields.Char("Année", default=lambda self: self.get_current_year())
    mois = fields.Selection(
        [('janvier', 'Janvier'), ('fevrirer', 'Février'), ('mars', 'Mars'),
         ('avril', 'Avril'), ('mai', 'Mai'), ('juin', 'Juin'),
         ('juillet', 'Juillet'), ('aout', 'Août'), ('septembre', 'Septembre'),
         ('octobre', 'Octobre'), ('novembre', 'Novembre'), ('decembre', 'Décembre')]
    )
    mois_year = fields.Char("Mois")
    suivi_lines = fields.One2many("usine.suivi.lines", "suivi_id", string="Lignes suivi")

    cumul_nb_sac = fields.Float("Nb. Sac de sel", compute="_all_values")
    cumul_sachet_production = fields.Float("Sachets Production", compute="_all_values")
    cumul_sachet_reconditionnement = fields.Float("Sachets Reconditionnement", compute="_all_values")
    cumul_sachet_total = fields.Float(" Total Sachets", store=True, compute="_all_values", tracking=5)
    cumul_nb_rouleaux_bandeaux = fields.Float("Nombre de rouleaux bandeaux", compute="_all_values")
    cumul_nb_rouleaux_bleute = fields.Float("Nombre de rouleaux bleuté", compute="_all_values")
    cumul_poids_total_bleute = fields.Float("Poids total bleuté (KG)", compute="_all_values")
    cumul_production_total = fields.Float("Production Totale")
    cumul_ratio = fields.Float("Ratio", store=True, compute="_all_values", tracking=5)

    def get_current_year(self):
        return datetime.today().year

    @api.model
    def create(self, vals):

        return super(models.Model, self).create(vals)

    @api.model
    def create(self, vals_list):
        self._all_values()
        return super(SuiviMateriaux, self).create(vals_list)

    def _all_values(self):


        for suivi in self:
            suivi.mois_year = suivi.mois+ " " + suivi.year
            cumul_nb_sac = cumul_sachet_production = cumul_sachet_reconditionnement = 0.0
            cumul_sachet_total = cumul_nb_rouleaux_bandeaux = cumul_nb_rouleaux_bleute = 0.0
            cumul_poids_total_bleute = cumul_production_total = cumul_ratio = 0.0

            for line in suivi.suivi_lines:
                cumul_nb_sac += line.nb_sac
                cumul_sachet_production += line.sachet_production
                cumul_sachet_reconditionnement += line.sachet_reconditionnement
                cumul_sachet_total += line.sachet_total
                cumul_nb_rouleaux_bandeaux += line.nb_rouleaux_bandeaux
                cumul_nb_rouleaux_bleute += line.nb_rouleaux_bleute
                cumul_poids_total_bleute += line.poids_total_bleute
                cumul_production_total += line.production_total
                cumul_ratio += line.ratio

            suivi.update({
                'cumul_nb_sac': cumul_nb_sac,
                'cumul_sachet_production': cumul_sachet_production,
                'cumul_sachet_reconditionnement': cumul_sachet_reconditionnement,
                'cumul_sachet_total': cumul_sachet_total,
                'cumul_nb_rouleaux_bandeaux': cumul_nb_rouleaux_bandeaux,
                'cumul_nb_rouleaux_bleute': cumul_nb_rouleaux_bleute,
                'cumul_poids_total_bleute': cumul_poids_total_bleute,
                'cumul_production_total': cumul_production_total,
                'cumul_ratio': cumul_production_total / cumul_poids_total_bleute
            })


class SuiviMateriauxLines(models.Model):
    _name = "usine.suivi.lines"

    semaine= fields.Integer("Semaine")
    nb_sac = fields.Float("Sel")
    sachet_production = fields.Float("Sachet (P)")
    sachet_reconditionnement = fields.Float("Sachet (R)")
    sachet_total = fields.Float(" Sachet (T)", store=True, compute='compute_sachet', tracking=5)
    nb_rouleaux_bandeaux = fields.Float("Bandeau (RL)")
    nb_rouleaux_bleute = fields.Float("Bleuté (RL) ")
    poids_total_bleute = fields.Float("Bleuté (kilo)")
    production_total = fields.Float("Prod. Total")
    ratio = fields.Float("Ratio", store=True, compute='compute_ratio', tracking=5)
    observation = fields.Text("Observation")
    suivi_id = fields.Many2one("usine.suivi", string="Suivi")

    @api.depends('poids_total_bleute', 'production_total')
    def compute_ratio(self):
        for material in self:
            if material.poids_total_bleute > 0 and material.production_total > 0:
                ratio = material.production_total / material.poids_total_bleute
                material.update({
                    'ratio': ratio
                })

    @api.depends('sachet_production', 'sachet_reconditionnement')
    def compute_sachet(self):
        for material in self:
            sachet_total = material.sachet_production + material.sachet_reconditionnement
            material.update({
                'sachet_total': sachet_total
            })


class RapportSuivi(models.Model):
    _name = "usine.rapport.suivi"

    cumul_nb_rouleaux_bleute = fields.Float("Nombre de rouleaux de bleute", store=True, compute='_amount_all',
                                            tracking=5)
    cumul_poids_total_bleute = fields.Float("Poids total Bleute", store=True, compute='_amount_all', tracking=5)
    cumul_production_total = fields.Float("Nombre de paquets", store=True, compute='_amount_all', tracking=5)
    cumul_ratio = fields.Float("Ratio", store=True, compute='_amount_all', tracking=5)

    def _amount_all(self):
        cumul_nb_rouleaux_bleute = cumul_poids_total_bleute = cumul_production_total = cumul_ratio = 0.0
        suivis = request.env['usine.suivi.materiaux'].sudo().search([])
        for line in suivis:
            cumul_nb_rouleaux_bleute += line.nb_rouleaux_bleute
            cumul_poids_total_bleute += line.poids_total_bleute
            cumul_production_total += line.production_total
            cumul_ratio += line.ratio
            self.update({
                'cumul_nb_rouleaux_bleute': cumul_nb_rouleaux_bleute,
                'cumul_poids_total_bleute': cumul_poids_total_bleute,
                'cumul_production_total': cumul_production_total,
                'cumul_ratio': cumul_ratio,
            })
