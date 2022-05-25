from odoo import models, fields

#creando un modelo a partir de una clase
class colores(models.Model):
    _name = 'colores'

    name = fields.Char(string="Color")