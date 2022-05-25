from odoo import models, fields

#creando un modelo a partir de una clase
class tallas(models.Model):
    _name = 'tallas'

    name = fields.Char(string="Talla")
    
    
    
