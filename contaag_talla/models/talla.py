from odoo import models, fields

#creando un modelo a partir de una clase
class tallas(models.Model):
    _name = 'tallas'

    name = fields.Char(string="Talla")
    
#crear campos del modulo
class producto_talla(models.Model):
    _inherit = 'product.template'

    talla_id = fields.Many2one(string='Talla', comodel_name='tallas')

class informe_talla(models.Model):
    _inherit = 'stock.quant'

    talla_info = fields.Many2one(string='Talla', related='product_id.talla_id')