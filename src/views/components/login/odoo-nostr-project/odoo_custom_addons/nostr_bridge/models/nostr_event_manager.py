# File: odoo_custom_addons/nostr_bridge/models/nostr_event_manager.py

from odoo import models, fields, api
import json
import time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import git
import os
import logging

_logger = logging.getLogger(__name__)

class NostrEventManager(models.AbstractModel):
    _name = 'nostr.event.manager'
    _description = 'Nostr Event Manager'

    @api.model
    def create_event(self, content, tags, private_key):
        pubkey = self.get_public_key(private_key)
        created_at = int(time.time())
        event_data = {
            "kind": 3120,
            "pubkey": pubkey,
            "created_at": created_at,
            "tags": tags,
            "content": json.dumps(content)
        }
        event_id = self.calculate_event_id(event_data)
        event_data["id"] = event_id
        event_data["sig"] = self.sign_event(event_data, private_key)
        _logger.info(event_data)
        return event_data

    @api.model
    def get_public_key(self, private_key):
        private_key_obj = ec.derive_private_key(int(private_key, 16), ec.SECP256K1())
        public_key = private_key_obj.public_key()
        return public_key.public_bytes(
            encoding=Encoding.X962,
            format=PublicFormat.UncompressedPoint
        )[1:].hex()

    @api.model
    def calculate_event_id(self, event_data):
        serialized = json.dumps([
            0,
            event_data['pubkey'],
            event_data['created_at'],
            event_data['kind'],
            event_data['tags'],
            event_data['content']
        ], separators=(',', ':'))
        return self.sha256(serialized)

    @api.model
    def sign_event(self, event_data, private_key):
        private_key_obj = ec.derive_private_key(int(private_key, 16), ec.SECP256K1())
        signature = private_key_obj.sign(
            bytes.fromhex(event_data['id']),
            ec.ECDSA(hashes.SHA256())
        )
        return signature.hex()

    @api.model
    def sha256(self, data):
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data.encode())
        return digest.finalize().hex()

    @api.model
    def create_git_event(self, repo_path, commit_hash):
        repo = git.Repo(repo_path)
        commit = repo.commit(commit_hash)
        
        content = {
            "action": "commit",
            "message": commit.message,
            "author": commit.author.name,
            "email": commit.author.email,
            "date": commit.authored_datetime.isoformat()
        }
        
        tags = [
            ["t", "commit"],
            ["h", commit_hash],
            ["n", repo.active_branch.name],
            ["m", commit.author.name],
            ["v", "1.0"],  # You might want to implement versioning
            ["r", repo.remotes.origin.url if repo.remotes else ""],
            ["p", self.get_public_key(self.env.user.nostr_private_key)],
            ["d", commit.message],
            ["s", "success"]
        ]
        
        return self.create_event(content, tags, self.env.user.nostr_private_key)

    @api.model
    def publish_event(self, event):
        nostr_adapter = self.env['nostr.adapter']
        return nostr_adapter.publish_event(event)

    @api.model
    def get_events(self, filters=None):
        nostr_adapter = self.env['nostr.adapter']
        return nostr_adapter.get_events(filters)
