# -*- coding: utf-8 -*-
from odoo import fields, api, models, _

class TypeOperation(models.Model):
    _name = "usine.type.operation"
    _description = "type_operation"

    name = fields.Char("Libellé",required=True)
    taux = fields.Float("Taux (CFA)",required=True)

