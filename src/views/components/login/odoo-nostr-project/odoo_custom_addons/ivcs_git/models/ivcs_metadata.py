from odoo import models, fields

class IVCSMetadata(models.Model):
    _name = 'ivcs.metadata'
    _description = 'IVCS Metadata'

    item_id = fields.Many2one('ivcs.item', string='Item')
    version_id = fields.Many2one('ivcs.version', string='Version')
    key = fields.Char('Key', required=True)
    value = fields.Text('Value', required=True)
