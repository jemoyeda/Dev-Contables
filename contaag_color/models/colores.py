from odoo import models, fields

#creando un modelo a partir de una clase
class colores(models.Model):
    _name = 'colores'

    name = fields.Char(string="Color")

#creando campos del modulo
class producto(models.Model):
    inherit = 'product.template'

    color_id = fields.Many2one('colores', string='Color')

class informe(models.Model):
    inherit = 'Quants'

    color_info = fields.Char(string='Color', related = 'product_id.color_id')
    
    
    
