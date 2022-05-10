from odoo import models, fields, api

class producto(models.Model):
    _inherit = 'product.template'
    
    modelo = fields.Char(string="Modelo")
    aplica = fields.Char(string="Aplica")
    capacidad = fields.Char(string="Capacidad")
    cantidad_unidad = fields.Float(string="Cantidad por Unidad")
    equipo = fields.Selection([('Si', 'Si'), ('No', 'No')])
    estado = fields.Selection([('Verificado', 'Verificado'), ('No verificado', 'No verificado')])
    marca = fields.Char(string="Marca")

class lote(models.Model):
    _inherit = 'stock.production.lot'
    
    lote_capacidad = fields.Char(string="Capacidad", related='product_id.capacidad')
    lote_equipos_compuestos = fields.Selection(string="Equipos Compuestos", related="product_id.equipo")
    lote_estado = fields.Selection([('Perfecto', 'Perfecto'),
                                    ('Defectuoso', 'Defectuoso'),
                                    ('Incompleto', 'Incompleto'),
                                    ('Con Parte(s) Defectuoso(s)', 'Con Parte(s) Defectuoso(s)'),
                                    ('En Reparacion', 'En Reparacion'),
                                    ('En Revision', 'En Revision'),
                                    ('Por Garantia', 'Por Garantia')
                                    ])
    lote_fecha_fabricacion = fields.Date(string="Fecha de fabricacion")
    lote_marca = fields.Char(string="Marca", related='product_id.marca')
    lote_modelo = fields.Char(string="Modelo", related='product_id.modelo')

class informe(models.Model):
    _inherit = 'stock.quant'
    
    informe_cantidad_unidad = fields.Float(related='product_id.cantidad_unidad', string="Cantidad por Unidad")
    informe_cantidad_total = fields.Float(string="Cantidad Total", compute='_compute_cantidad_total')
    informe_capacidad = fields.Char(related='product_id.capacidad', string="Capacidad")
    informe_equipo_compuesto = fields.Selection(related='product_id.equipo', string="Equipo Compuesto")
    informe_estado = fields.Selection(related='product_id.estado', string="Estado")
    informe_marca = fields.Char(related='product_id.marca', string="Marca")
    informe_modelo = fields.Char(related='product_id.modelo', string="Modelo")
    informe_fecha_fabricacion = fields.Date(related='lot_id.lote_fecha_fabricacion', string="Fecha de fabricacion")
    
    @api.depends('available_quantity', 'informe_cantidad_unidad')
    def _compute_cantidad_total(self):
        for record in self:
            if record['informe_cantidad_unidad'] == 0 :
                record['informe_cantidad_total'] = record['available_quantity']
            else:
                record['informe_cantidad_total'] = record['informe_cantidad_unidad'] * record['available_quantity']