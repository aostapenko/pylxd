# Copyright (c) 2016 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import hashlib

from pylxd import model
from pylxd.operation import Operation


class Image(model.Model):
    """A LXD Image."""
    aliases = model.Attribute(readonly=True)
    auto_update = model.Attribute(optional=True)
    architecture = model.Attribute(readonly=True)
    cached = model.Attribute(readonly=True)
    created_at = model.Attribute(readonly=True)
    expires_at = model.Attribute(readonly=True)
    filename = model.Attribute(readonly=True)
    fingerprint = model.Attribute(readonly=True)
    last_used_at = model.Attribute(readonly=True)
    properties = model.Attribute()
    public = model.Attribute()
    size = model.Attribute(readonly=True)
    uploaded_at = model.Attribute(readonly=True)
    update_source = model.Attribute(readonly=True)

    @property
    def api(self):
        return self.client.api.images[self.fingerprint]

    @classmethod
    def get(cls, client, fingerprint):
        """Get an image."""
        response = client.api.images[fingerprint].get()

        image = cls(client, **response.json()['metadata'])
        return image

    @classmethod
    def get_by_alias(cls, client, alias):
        """Get an image by its alias."""
        response = client.api.images.aliases[alias].get()

        fingerprint = response.json()['metadata']['target']
        return cls.get(client, fingerprint)

    @classmethod
    def all(cls, client):
        """Get all images."""
        response = client.api.images.get()

        images = []
        for url in response.json()['metadata']:
            fingerprint = url.split('/')[-1]
            images.append(cls(client, fingerprint=fingerprint))
        return images

    @classmethod
    def create(cls, client, image_data, public=False, wait=False):
        """Create an image."""
        fingerprint = hashlib.sha256(image_data).hexdigest()

        headers = {}
        if public:
            headers['X-LXD-Public'] = '1'
        response = client.api.images.post(
            data=image_data, headers=headers)

        if wait:
            Operation.wait_for_operation(client, response.json()['operation'])
        return cls(client, fingerprint=fingerprint)

    def export(self):
        """Export the image."""
        response = self.api.export.get()
        return response.content

    def add_alias(self, name, description):
        """Add an alias to the image."""
        self.client.api.images.aliases.post(json={
            'description': description,
            'target': self.fingerprint,
            'name': name
        })

        # Update current aliases list
        self.aliases.append({
            'description': description,
            'target': self.fingerprint,
            'name': name
        })

    def delete_alias(self, name):
        """Delete an alias from the image."""
        self.client.api.images.aliases[name].delete()

        # Update current aliases list
        la = [a['name'] for a in self.aliases]
        try:
            del self.aliases[la.index(name)]
        except ValueError:
            pass
