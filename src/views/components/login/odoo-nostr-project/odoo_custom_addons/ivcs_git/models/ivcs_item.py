from odoo import _, models, fields, api
from odoo.exceptions import UserError
import git
import os
import logging
import uuid
import json
from datetime import datetime
from difflib import unified_diff

_logger = logging.getLogger(__name__)

class IVCSItem(models.Model):
    _name = 'ivcs.item'
    _description = 'IVCS Item'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    current_version_id = fields.Many2one('ivcs.version', string='Current Version')
    version_ids = fields.One2many('ivcs.version', 'item_id', string='Versions')
    metadata_ids = fields.One2many('ivcs.metadata', 'item_id', string='Metadata')
    repo_path = fields.Char('Repository Path', compute='_compute_repo_path')
    current_branch = fields.Char('Current Branch', default='main')
    commit_ids = fields.One2many('ivcs.commit', 'item_id', string='Commits')

    @api.depends('name')
    def _compute_repo_path(self):
        for item in self:
            item.repo_path = os.path.join(self.env['ir.config_parameter'].sudo().get_param('ivcs.repo_base_path', '/opt/ivcs_repos'), f"item_{item.id}")

    def _initialize_repository(self):
        if not os.path.exists(self.repo_path):
            os.makedirs(self.repo_path)
            repo = git.Repo.init(self.repo_path)
            readme_path = os.path.join(self.repo_path, 'README.md')
            with open(readme_path, 'w') as f:
                f.write(f"# {self.name}\n\n{self.description}")
            repo.index.add(['README.md'])
            repo.index.commit("Initial commit")
            self._create_initial_version()
            self._create_commit("Initial commit")

    def _create_commit(self, message):
        commit = self.env['ivcs.commit'].create({
            'item_id': self.id,
            'message': message,
            'branch': self.current_branch,
            'commit_hash': self._get_latest_commit_hash(),
        })
        return commit

    def _get_latest_commit_hash(self):
        repo = git.Repo(self.repo_path)
        return repo.head.commit.hexsha

    def create_branch(self, branch_name):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        current_branch = repo.active_branch.name
        if branch_name not in repo.heads:
            repo.create_head(branch_name)
            self.current_branch = branch_name
            repo.git.checkout(branch_name)
            self._create_git_event('branch', branch_name=branch_name)
            return self._return_success('Branch Created', f'Branch {branch_name} has been created and checked out.')
        else:
            return self._return_warning('Branch Exists', f'Branch {branch_name} already exists.')

    def switch_branch(self, branch_name):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        if branch_name in repo.heads:
            repo.git.checkout(branch_name)
            self.current_branch = branch_name
            return self._return_success('Branch Switched', f'Switched to branch: {branch_name}')
        else:
            return self._return_warning('Branch Not Found', f'Branch {branch_name} does not exist.')

    def merge_branches(self, source_branch, target_branch):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        if source_branch not in repo.heads or target_branch not in repo.heads:
            return self._return_error('Branch Not Found', 'One or both branches do not exist.')

        current_branch = repo.active_branch.name
        repo.git.checkout(target_branch)
        try:
            repo.git.merge(source_branch)
            merge_commit = self._create_commit(f"Merge {source_branch} into {target_branch}")
            self._create_git_event('merge', source_branch=source_branch, target_branch=target_branch)
            return self._return_success('Branches Merged', f'Branch {source_branch} has been merged into {target_branch}.')
        except git.GitCommandError as e:
            if 'CONFLICT' in str(e):
                return self._return_warning('Merge Conflict', f'There are conflicts merging {source_branch} into {target_branch}. Please resolve conflicts manually.')
            else:
                return self._return_error('Merge Failed', str(e))
        finally:
            repo.git.checkout(current_branch)

    def rebase_branch(self, branch_name, onto_branch):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        if branch_name not in repo.heads or onto_branch not in repo.heads:
            return self._return_error('Branch Not Found', 'One or both branches do not exist.')

        current_branch = repo.active_branch.name
        try:
            repo.git.checkout(branch_name)
            repo.git.rebase(onto_branch)
            self._create_commit(f"Rebased {branch_name} onto {onto_branch}")
            return self._return_success('Rebase Completed', f'Successfully rebased {branch_name} onto {onto_branch}.')
        except git.GitCommandError as e:
            if 'CONFLICT' in str(e):
                return self._return_warning('Rebase Conflict', f'There are conflicts rebasing {branch_name} onto {onto_branch}. Please resolve conflicts manually.')
            else:
                return self._return_error('Rebase Failed', str(e))
        finally:
            repo.git.checkout(current_branch)

    def generate_diff(self, file_path, old_commit, new_commit):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        try:
            old_content = repo.git.show(f'{old_commit}:{file_path}')
            new_content = repo.git.show(f'{new_commit}:{file_path}')
            diff = list(unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}'
            ))
            return ''.join(diff)
        except git.GitCommandError as e:
            _logger.error(f"Failed to generate diff: {str(e)}")
            return None

    def handle_merge_conflict(self, file_path):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        try:
            with open(os.path.join(self.repo_path, file_path), 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            _logger.error(f"Failed to read conflicted file: {str(e)}")
            return None

    def action_create_file(self):
        self.ensure_one()
        return {
            'name': _('Create File'),
            'type': 'ir.actions.act_window',
            'res_model': 'ivcs.create.file.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_item_id': self.id},
        }

    def _create_git_event(self, event_type, **kwargs):
        nostr_event_manager = self.env['nostr.event.manager']
        if event_type == 'commit':
            event = nostr_event_manager.create_git_event(self.repo_path, kwargs.get('commit_hash'))
        elif event_type == 'branch':
            event = nostr_event_manager.create_branch_event(self.repo_path, kwargs.get('branch_name'))
        elif event_type == 'merge':
            event = nostr_event_manager.create_merge_event(self.repo_path, kwargs.get('source_branch'), kwargs.get('target_branch'))
        elif event_type == 'tag':
            event = nostr_event_manager.create_tag_event(self.repo_path, kwargs.get('tag_name'), kwargs.get('tag_message'))
        else:
            raise UserError(_("Unsupported git event type"))
        
        nostr_event_manager.publish_event(event)

    def create_file(self, filename, content):
        _logger.info(f"Filename type: {type(filename)}")
        _logger.info(f"Content type: {type(content)}")
        self.ensure_one()
        file_path = os.path.join(self.repo_path, filename)
        
        if os.path.exists(file_path):
            raise UserError(_("A file with this name already exists."))
        
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            
            repo = git.Repo(self.repo_path)
            repo.index.add([filename])
            commit = repo.index.commit(f"Add new file: {filename}")
            
            _logger.info(f"Commit variable type: {type(commit)}")
            _logger.info(f"commit.hexsha type: {type(commit.hexsha)}")

            # Create and publish Nostr event for the commit
            self._create_git_event('commit', commit_hash=str(commit.hexsha))
            
            # Sync with remote repository
            self.sync_repository()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("File Created"),
                    'message': _("File %s has been created and committed.") % filename,
                    'type': 'success',
                }
            }
        except Exception as e:
            _logger.error(f"Failed to create file: {str(e)}")
            raise UserError(_("Failed to create file: %s") % str(e))    
        
    @api.model
    def create(self, vals):
        item = super(IVCSItem, self).create(vals)
        item._initialize_repository()
        return item

    def verify_remote_url(self):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        remote_url = repo.remotes.origin.url
        
        # Remove any existing token from the URL
        from urllib.parse import urlparse, urlunparse
        parsed_url = urlparse(remote_url)
        clean_url = urlunparse(parsed_url._replace(netloc=parsed_url.netloc.split('@')[-1]))
    
        # Update the remote URL without the token
        repo.remotes.origin.set_url(clean_url)
        
        _logger.info(f"Verified remote URL: {clean_url}")
        return self._return_success('Remote URL Verified', 'The remote URL has been verified and updated if necessary.')

    def _create_initial_version(self):
        version = self.env['ivcs.version'].create({
            'item_id': self.id,
            'name': 'v1.0',
            'description': 'Initial version',
        })
        self.current_version_id = version.id

    def setup_git_auth(self):
        git_token = self.env['ir.config_parameter'].sudo().get_param('ivcs_git.github_token')
        if not git_token:
            raise UserError(_("GitHub token not configured. Please set it in the settings."))
        
        repo = git.Repo(self.repo_path)
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', 'Odoo IVCS')
            git_config.set_value('user', 'email', 'odoo@example.com')
        
        remote_url = repo.remotes.origin.url
        if not remote_url.startswith('https://'):
            raise UserError(_("Remote URL is not using HTTPS. Please update the remote URL."))
        
        # Parse the existing URL
        from urllib.parse import urlparse, urlunparse
        parsed_url = urlparse(remote_url)
        
        # Reconstruct the URL with the token
        new_netloc = f"{git_token}@{parsed_url.netloc}"
        new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
        
        # Set the new URL for the origin remote
        repo.remotes.origin.set_url(new_url)
        
        # Log the URL (without the token) for debugging
        _logger.info(f"Updated remote URL: https://{parsed_url.netloc}{parsed_url.path}")
    
    @api.model
    def _sync_repositories(self):
        items = self.search([])
        for item in items:
            repo = git.Repo(item.repo_path)
            try:
                repo.remotes.origin.pull()
                _logger.info(f"Successfully synced repository for item {item.name}")
            except Exception as e:
                _logger.error(f"Failed to sync repository for item {item.name}: {str(e)}")

    def sync_repository(self):
        self.ensure_one()
        self.verify_remote_url()
        self.setup_git_auth()
        try:
            repo = git.Repo(self.repo_path)
            if not repo.remotes:
                return self._return_warning('No Remote Repository', 'This repository does not have a remote configured. Please add a remote repository first.')
            
            origin = repo.remotes.origin
            if not origin.exists():
                return self._return_warning('Remote Not Found', 'The remote "origin" does not exist. Please configure the remote repository.')
            
            # Fetch the latest changes
            origin.fetch()
            
            # Get the current branch name
            current_branch = str(repo.active_branch)
            
            # Check if the remote branch exists
            remote_branch = f'origin/{current_branch}'
            if remote_branch not in [str(ref) for ref in repo.references]:
                # If remote branch doesn't exist, push the current branch to create it
                origin.push(current_branch)
                return self._return_success('Branch Created', f'The branch "{current_branch}" has been created on the remote repository.')
            
            # Check if we need to pull changes
            if repo.is_dirty() or repo.untracked_files:
                # There are local changes, commit them first
                repo.git.add(A=True)
                repo.index.commit("Local changes before sync")
            
            # Pull changes
            origin.pull(current_branch)
            
            # Push any local commits
            origin.push(current_branch)
            
            self._create_git_event('commit', commit_hash=str(repo.head.commit.hexsha))
            
            return self._return_success('Repository Synced', 'The repository has been successfully synced.')
        except git.GitCommandError as e:
            _logger.error(f"Git command error: {str(e)}")
            return self._return_error('Sync Failed', f'Git command error: {str(e)}')
        except ValueError as e:
            _logger.error(f"Value error: {str(e)}")
            return self._return_error('Sync Failed', f'Value error: {str(e)}')
        except Exception as e:
            _logger.error(f"Error syncing repository: {str(e)}")
            return self._return_error('Sync Failed', f'An unexpected error occurred: {str(e)}')

    def _return_warning(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(message),
                'type': 'warning',
            }
        }

    def _return_success(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(message),
                'type': 'success',
            }
        }

    def _return_error(self, title, message):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': _(message),
                'type': 'danger',
            }
        }

    def setup_git_auth(self):
        git_token = self.env['ir.config_parameter'].sudo().get_param('ivcs_git.github_token')
        if not git_token:
            raise UserError(_("GitHub token not configured. Please set it in the settings."))
        
        repo = git.Repo(self.repo_path)
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'name', 'Odoo IVCS')
            git_config.set_value('user', 'email', 'odoo@example.com')
        
        remote_url = repo.remotes.origin.url
        if not remote_url.startswith('https://'):
            raise UserError(_("Remote URL is not using HTTPS. Please update the remote URL."))
        
        new_url = f'https://{git_token}@' + remote_url[8:]
        repo.remotes.origin.set_url(new_url)

    def action_open_create_branch_wizard(self):
        self.ensure_one()
        return {
            'name': _('Create Branch'),
            'type': 'ir.actions.act_window',
            'res_model': 'ivcs.create.branch.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_item_id': self.id},
        }

    def add_remote(self, remote_url, remote_name='origin'):
        self.ensure_one()
        try:
            repo = git.Repo(self.repo_path)
            if remote_name in repo.remotes:
                repo.delete_remote(remote_name)
            repo.create_remote(remote_name, remote_url)
            return self._return_success('Remote Added', 'Remote repository has been added successfully.')
        except Exception as e:
            return self._return_error('Failed to Add Remote', f'An error occurred while adding the remote: {str(e)}')

    def action_open_add_remote_wizard(self):
        self.ensure_one()
        return {
            'name': _('Add Remote Repository'),
            'type': 'ir.actions.act_window',
            'res_model': 'ivcs.add.remote.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_item_id': self.id},
        }

    def create_branch(self, branch_name):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        repo.git.checkout('-b', branch_name)
        self._create_git_event('branch', branch_name=branch_name)
        return self._return_success('Branch Created', f'Branch {branch_name} has been created.')

    def merge_branches(self, source_branch, target_branch):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        repo.git.checkout(target_branch)
        repo.git.merge(source_branch)
        self._create_git_event('merge', source_branch=source_branch, target_branch=target_branch)
        return self._return_success('Branches Merged', f'Branch {source_branch} has been merged into {target_branch}.')

    def create_tag(self, tag_name, tag_message):
        self.ensure_one()
        repo = git.Repo(self.repo_path)
        repo.create_tag(tag_name, message=tag_message)
        self._create_git_event('tag', tag_name=tag_name, tag_message=tag_message)
        return self._return_success('Tag Created', f'Tag {tag_name} has been created.')


