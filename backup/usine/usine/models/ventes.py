# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import UserError
from odoo.http import request

STATUT_ENCAISSEMENT = [
    ('encaisse', 'Encaissé'),
    ('pas_encaisse', 'Pas Encaissé'),
]


class TypeArticle(models.Model):
    _name = "usine.type.article"
    _description = "Type Article"

    name = fields.Char("Article", required=True)
    description = fields.Char("Description", required=True)
    prix = fields.Float("Prix")

    # taxes_id = fields.Many2many('account.tax', string='Taxe',)
    # tax_id = fields.Many2many('account.tax', 'article_tax_rel', 'article_id', 'tax_id', string='Taxes')

    @api.model
    def unlink(self):
        if self.id in (1, 2):
            raise UserError(_('Il n\'est pas possible de supprimer cet article.'))


class Vente(models.Model):
    _name = "usine.vente"
    _description = "Ventes Usine"

    name = fields.Char("Numéro", readonly=True, required=True, copy=False, default="Nouveau")
    date_vente = fields.Date("Date", required=True, default=fields.Date.context_today)
    vente_lines = fields.One2many("usine.vente.lines", "vente_id", string="Lignes vente")
    synthese_lines = fields.One2many("usine.synthese", "vente_id", string="Synthèse Vente", readonly=True)
    caissier = fields.Many2one('res.users', string='Caissier', index=True, tracking=2,
                               default=lambda self: self.env.user)
    status = fields.Selection([('encaisse', 'Encaissé'), ('non_encaisse', 'Non Encaissé')], string="Etat",
                              default='non_encaisse')
    montant_total = fields.Float("Montant Total", compute="_compute_montant_total")

    @api.model_create_multi
    def create(self, vals_list):
        vente = super(Vente, self).create(vals_list)
        vente.name = self.env['ir.sequence'].next_by_code('numero.vente')
        return vente

    def _compute_montant_total(self):
        for vente in self:
            montant_total = vente.montant_total = 0
            for line in vente.vente_lines:
                montant_total += line.montant_total
            vente.montant_total = montant_total

    """year = fields.Char("Année", default=lambda self: self.get_current_year())
    mois = fields.Selection(
        [('janvier', 'Janvier'), ('fevrier', 'Février'), ('mars', 'Mars'),
         ('avril', 'Avril'), ('mai', 'Mai'), ('juin', 'Juin'),
         ('juillet', 'Juillet'), ('aout', 'Août'), ('septembre', 'Septembre'),
         ('octobre', 'Octobre'), ('novembre', 'Novembre'), ('decembre', 'Décembre')]
    )

    payment_lines = fields.One2many("usine.payment.vendeur.lines", "pointage_id", string="Lignes payment",readonly=True)
    amount_total = fields.Float(string='Montal Total', store=True, compute='_amount_all', tracking=5)

    total_package = fields.Integer(string='Total paquets', store=True, compute='_amount_all', tracking=5)
    total_vendeur = fields.Integer(string='Total vendeurs', store=True, compute='_amount_all', tracking=5)


    @api.depends('pointage_lines.total')
    def _amount_all(self):
    
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
        return True"""

    def encaisser(self):
        self.synthese()
        self.status = 'encaisse'
        vendeurs_lines = self.env['usine.synthese'].search([('vente_id', '=', self.id)])
        self.env['usine.etat.caisse'].sudo().search([('vente_id', '=', self.id)]).unlink()
        self.env['usine.appro.caisse'].sudo().search([('numero_piece_appro', '=', self.name)]).unlink()
        for vendeur_line in vendeurs_lines:
            vals = {
                'date_vente': self.date_vente,
                'vente_id': self.id,
                'description': vendeur_line.vendeur_id.id,
                'montant': vendeur_line.recette_net,
                'caissier':self.caissier.id,
                'name':self.name
            }

            self.env['usine.etat.caisse'].sudo().create(vals)
            if vendeur_line.recette_net > 0:
                vals_appro = {
                    'montant':vendeur_line.recette_net,
                    'numero_piece_appro':self.name,
                    'description':vendeur_line.vendeur_id.name,
                    'caissier':self.caissier.id,
                    'date':self.date_vente,
                }
                self.env['usine.appro.caisse'].sudo().create(vals_appro)

        return True

    def synthese(self):
        vendeurs = self.env['usine.vendeur'].search([])
        self.env['usine.synthese'].sudo().search([]).unlink()
        self.ensure_one()
        for vendeur in vendeurs:
            montant = creance = credit = 0
            for vente in self:
                for line in vente.vente_lines:
                    if vendeur.id == line.vendeur.id:
                        if line.type_article_id.id == 1:
                            # montant += line.montant_total
                            credit += line.montant_total
                        elif line.type_article_id.id == 2:
                            # montant += line.montant_total
                            creance += line.montant_total
                        else:
                            montant += line.montant_total
                    recette_net = montant + creance - credit

                    vals = {
                        'vendeur_id': vendeur.id,
                        'creance_recouvre': creance,
                        'vente_credit': credit,
                        'recette_net': recette_net,
                        'total_vendu': montant,
                        'vente_id': self.id
                    }

                    if montant == creance == credit == 0:
                        continue
                self.env['usine.synthese'].sudo().create(vals)
        for line in self.synthese_lines:
            if line.recette_net == 0:
                self.env['usine.synthese'].sudo().search([('id', '=', line.id)]).unlink()

        return True

class SortieCaiss(models.Model):
    _name = "usine.sortie.caisse"
    _description = "Appro Caisse"

    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    numero_piece_sortie = fields.Char(string="Numéro pièce appro", readonly=True, required=True, copy=False, default="New")
    description = fields.Char("Description")
    montant = fields.Float("Montant")
    caissier = fields.Many2one('res.users', string='Caissier', index=True, tracking=2,
                               default=lambda self: self.env.user)



    @api.model_create_multi
    def create(self, vals_list):
        caisse = self.env['usine.caisse'].sudo().search([])
        sortie_caisse = super(SortieCaiss, self).create(vals_list)
        sortie_caisse.numero_piece_sortie = self.env['ir.sequence'].next_by_code('numero.piece.sortie')
        montant = caisse.montant - sortie_caisse["montant"]

        caisse.update({'montant': montant})
        return sortie_caisse


class ApproCaiss(models.Model):
    _name = "usine.appro.caisse"
    _description = "Appro Caisse"

    date = fields.Date("Date",required=True, default=fields.Date.context_today)
    numero_piece_appro = fields.Char(string="Numéro pièce appro", readonly=True, required=True, copy=False, default="New")
    description = fields.Char("Description")
    montant = fields.Float("Montant")
    caissier = fields.Many2one('res.users', string='Caissier', index=True, tracking=2,
                               default=lambda self: self.env.user)


    @api.model_create_multi
    def create(self, vals_list):
        caisse = self.env['usine.caisse'].sudo().search([])
        appro = super(ApproCaiss, self).create(vals_list)
        appro.numero_piece_appro = self.env['ir.sequence'].next_by_code('numero.piece.appro')
        montant = caisse.montant + appro["montant"]

        caisse.update({'montant': montant})
        return appro


class VenteLines(models.Model):
    _name = "usine.vente.lines"

    numero = fields.Integer(string="#")
    vendeur = fields.Many2one('usine.vendeur', 'Vendeur', required=True)
    date = fields.Date("Date")
    vehicule_id = fields.Many2one("fleet.vehicle", "Véhicule", required=True)
    type_article_id = fields.Many2one("usine.type.article", "Article", required=True)
    prix_unitaire = fields.Float("Prix unitaire", required=True)
    quantite = fields.Integer("Quantité", required=True)
    # taxe = fields.Many2many('usine.type.article', string='Taxe',)
    montant_total = fields.Float("Montant total vendu")
    status_encaissement = fields.Selection(STATUT_ENCAISSEMENT, string="Status Encaissement", store=True,
                                           readonly=True, copy=False, tracking=True)
    vente_id = fields.Many2one("usine.vente", string="Vente")

    @api.onchange('type_article_id', 'quantite', 'prix_unitaire')
    def compute_total(self):
        for line in self:
            if line.type_article_id.id != 100 and line.type_article_id.id != 101:
                line.prix_unitaire = line.type_article_id.prix
                line.montant_total = line.prix_unitaire * line.quantite
            else:
                line.prix_unitaire = 0
                line.quantite = 1

    """type_operation = fields.Many2one("usine.type.operation", "Type opération")
    package_number = fields.Integer("Nombre de paquets vendus")
    commission = fields.Float("Commission")
    vente_id = fields.Many2one("usine.vente", string="Vente")
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
                emp.total = emp.commission * emp.package_number - emp.carburant"""


class Synthese(models.Model):
    _name = "usine.synthese"
    _description = "Synthese"

    vendeur_id = fields.Many2one("usine.vendeur", string="Vendeur")
    total_vendu = fields.Float("Vente au Comptant (A)")
    vente_credit = fields.Float("Vente à Crédit (B)")
    creance_recouvre = fields.Float("Créances recouvres (C)")
    recette_net = fields.Float("RECETTE NET (A+C-B)")
    vente_id = fields.Many2one("usine.vente", string="Vente")


class EtatCaisse(models.Model):
    _name = "usine.etat.caisse"
    _description = "Etat Caisse"

    date_vente = fields.Date("Date")
    name = fields.Char(string="Vente", readonly=True, required=True, copy=False, default='New')
    description = fields.Many2one('usine.vendeur', "Vendeur")
    montant = fields.Float("Montant")
    caissier = fields.Many2one('res.users', string='Caissier', index=True, tracking=2,
                               default=lambda self: self.env.user)
    vente_id = fields.Many2one("usine.vente", string="Vente")

    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('numero.piece') or 'New'
        result = super(EtatCaisse, self).create(vals)
        return result


class Caisse(models.Model):
    _name = "usine.caisse"
    _description = "Caisse"

    name = fields.Char("Libellé")
    montant = fields.Float('Montant')

    def unlink(self):
        raise UserError(_('Vous ne pouvez pas supprimer cette ligne'))
