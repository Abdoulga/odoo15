# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from datetime import datetime

from odoo.http import request


class Article(models.Model):
    _name = "usine.article"

    _description = "usine.article"

    name = fields.Char("Nom", require=True)
    reference = fields.Char("Référence", require=True)
    description = fields.Char("Description")
    prix = fields.Float("Prix de vente")
    quantite = fields.Integer("Quantité en stock")
    unite = fields.Many2one(
        'uom.uom', 'Unité de compte', required=True,
        help="Default unit of measure used for all stock operations.",
        default=lambda self: self.env['uom.uom'].search([('id','=',1)])
    )

    def update_quantite(self,quantite):
        self.quantite = quantite



class Entree(models.Model):
    _name = "usine.entree"

    _description = "usine.entree"

    user = fields.Many2one('res.users', string='Utilisateur', index=True, tracking=2,
                           default=lambda self: self.env.user)
    name = "Entrée Stock"
    date_entree = fields.Date("Date",required=True, default=fields.Date.context_today)
    ref_article = fields.Many2one("usine.article", "Référence Article",required=True)
    quantite = fields.Integer("Quantité entrée (nombre de packs)",required=True)
    qte_dispo = fields.Integer("Disponible",default=0)

    @api.onchange('type_article_id')
    def get_quantity(self):
        for line in self:
            if self.type_article_id:
                article = self.env['usine.article'].search(['id','=',self.type_article_id.id])
                self.qte_dispo = article.quantite

    @api.model_create_multi
    def create(self, vals_list):
        entree = super(Entree, self).create(vals_list)
        article = request.env['usine.article'].sudo().search([('id', '=', entree["ref_article"].id)])
        total = article.quantite
        for vals in entree:
            total = total + vals.quantite
            article = article.update_quantite(max(total,0))
        vals_mv = {
            'date': entree["date_entree"],
            'ref_article':entree["ref_article"].id,
            'quantite':entree["quantite"],
            'type': 'sortie'

        }
        self.env['usine.mouvement.stock'].sudo().create(vals_mv)
        return entree

    def unlink(self):
        article = request.env['usine.article'].sudo().search([('id', '=', self.ref_article.id)])
        total = article.quantite
        for vals in self:
            total = total - vals.quantite
            article = article.update_quantite(max(total,0))
        return models.Model.unlink(self)


class Sortie(models.Model):
    _name = "usine.sortie"

    _description = "usine.sortie"
    user = fields.Many2one('res.users', string='Utilisateur', index=True, tracking=2,
                           default=lambda self: self.env.user)
    name = "Sortie Stock"
    date_sortie = fields.Date("Date",required=True, default=fields.Date.context_today)
    ref_article = fields.Many2one("usine.article", "Référence Article",required=True)
    quantite = fields.Integer("Quantité chargés (nombre de packs)",required=True)
    vehicule_id = fields.Many2one("fleet.vehicle", "Véhicule",required=True)
    vendeur_id = fields.Many2one("usine.vendeur", "Chauffeur/Vendeurs ",required=True)

    @api.model_create_multi
    def create(self, vals_list):
        sortie = super(Sortie, self).create(vals_list)
        #entree = request.env['usine.entree'].sudo().search([('id', '=', entree_id)])
        article = request.env['usine.article'].sudo().search([('id', '=', sortie["ref_article"].id)])
        total = article.quantite
        for vals in sortie:
            total = total - vals.quantite
            article = article.update_quantite(max(total,0))
        vals_mv = {
            'date': sortie["date_sortie"],
            'ref_article': sortie["ref_article"].id,
            'quantite': sortie["quantite"],
            'type':'sortie'

        }
        self.env['usine.mouvement.stock'].sudo().create(vals_mv)
        return sortie

    def unlink(self):
        #line = request.env['usine.entree'].sudo().search([('id', '=', self.id)])
        article = request.env['usine.article'].sudo().search([('id', '=', self.ref_article.id)])
        total = article.quantite
        for vals in self:
            total = total + vals.quantite
            article = article.update_quantite(max(total,0))
        return models.Model.unlink(self)



class MouvementStock(models.Model):
    _name = "usine.mouvement.stock"
    user = fields.Many2one('res.users', string='Utilisateur', index=True, tracking=2,
                           default=lambda self: self.env.user)
    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    ref_article = fields.Many2one("usine.article", "Référence Article", required=True)
    quantite = fields.Integer("Quantité chargés (nombre de packs)", required=True)
    type = fields.Char("Type Mouvement")