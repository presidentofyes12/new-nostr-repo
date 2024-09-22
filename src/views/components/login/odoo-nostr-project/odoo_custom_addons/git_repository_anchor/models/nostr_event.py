from odoo import models, fields, api
from nostr.event import Event
import json
import logging

_logger = logging.getLogger(__name__)

class NostrEvent(models.Model):
    _name = 'nostr.event'
    _description = 'Nostr Event'

    event_id = fields.Char(string='Event ID', required=True)
    kind = fields.Integer(string='Event Kind', required=True)
    content = fields.Text(string='Content', required=True)
    tags = fields.Text(string='Tags')
    public_key = fields.Char(string='Public Key', required=True)
    created_at = fields.Integer(string='Created At', required=True)
    signature = fields.Char(string='Signature', required=True)

    @api.model
    def create_and_publish(self, event):
        vals = {
            'event_id': event.id,
            'kind': event.kind,
            'content': event.content,
            'tags': json.dumps(event.tags),
            'public_key': event.public_key,
            'created_at': event.created_at,
            'signature': event.signature,
        }
        nostr_event = self.create(vals)
        # Here you would typically publish the event to Nostr relays
        # For demonstration purposes, we'll just log it
        _logger.info(f"Published Nostr event: {event.to_message()}")
        return nostr_event
