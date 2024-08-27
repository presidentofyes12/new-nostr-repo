from odoo import models, fields, api
from odoo.exceptions import UserError
import git
import os

class IVCSVersion(models.Model):
    _name = 'ivcs.version'
    _description = 'IVCS Version'

    name = fields.Char('Version Name', required=True)
    description = fields.Text('Description')
    item_id = fields.Many2one('ivcs.item', string='Item', required=True)
    parent_id = fields.Many2one('ivcs.version', string='Parent Version')
    commit_hash = fields.Char('Commit Hash', readonly=True)
    create_date = fields.Datetime('Created On', readonly=True, default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('released', 'Released'),
        ('deprecated', 'Deprecated')
    ], string='Status', default='draft')
    metadata_ids = fields.One2many('ivcs.metadata', 'version_id', string='Metadata')

    @api.model
    def create(self, vals):
        version = super(IVCSVersion, self).create(vals)
        version._create_commit()
        return version

    def _create_commit(self):
        repo = git.Repo(self.item_id.repo_path)
        readme_path = os.path.join(self.item_id.repo_path, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(f"# {self.item_id.name} - {self.name}\n\n{self.description}")
        repo.index.add(['README.md'])
        commit = repo.index.commit(f"Version {self.name}: {self.description}")
        self.commit_hash = commit.hexsha

    def release_version(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft versions can be released.")
        self.state = 'released'

    def deprecate_version(self):
        self.ensure_one()
        if self.state != 'released':
            raise UserError("Only released versions can be deprecated.")
        self.state = 'deprecated'
