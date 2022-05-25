from odoo import models, fields 

#creando campos del modulo
class producto(models.Model):
    inherit = 'product.product'

    color_id = fields.Many2one('colores', string='Color')