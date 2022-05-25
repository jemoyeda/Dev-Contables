from odoo import models, fields 

#creando campos del modulo
class producto(models.Model):
    inherit = 'product.template'

    color_id = fields.Many2one(comodel_name='colores', string='Color')