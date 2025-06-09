from odoo import fields, models, api



class trainingCourse(models.Model):
    _name = 'training.courses'
    # _inherit = ['product.catalog.mixin', 'stock.picking']

    name=fields.Char(string="Name")