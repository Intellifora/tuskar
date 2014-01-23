# -*- encoding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Contains transfer objects for use with WSME REST APIs. The objects in this
module also contain the translations between the REST transfer objects and
the internal Tuskar domain model.
"""

import logging
from wsme import types as wtypes

from tuskar.db.sqlalchemy import models as db_models


LOG = logging.getLogger(__name__)


class Base(wtypes.Base):
    """Base functionality for all API models.

    This class should never be directly instantiated. Subclasses must be sure
    to define an attribute named _db_class for the to_db_model to use
    when instantiating DB models.
    """

    @classmethod
    def from_db_model(cls, db_model, skip_fields=None):
        """Returns the database representation of the given transfer object."""
        skip_fields = skip_fields or []
        data = dict((k, v) for k, v in db_model.as_dict().items()
                    if k not in skip_fields)
        return cls(**data)

    def to_db_model(self, omit_unset=False, skip_fields=None):
        """Converts this object into its database representation."""
        skip_fields = skip_fields or []
        attribute_names = [a.name for a in self._wsme_attributes
                           if a.name not in skip_fields]

        if omit_unset:
            attribute_names = [n for n in attribute_names
                               if getattr(self, n) != wtypes.Unset]

        values = dict((name, self._lookup(name)) for name in attribute_names)
        db_object = self._db_class(**values)
        return db_object

    def _lookup(self, key):
        """Looks up a key, translating WSME's Unset into Python's None.

        :return: value of the given attribute; None if it is not set
        """
        value = getattr(self, key)
        if value == wtypes.Unset:
            value = None
        return value


class ResourceCategory(Base):
    """Transfer object for resource categories."""

    _db_class = db_models.ResourceCategory

    id = int
    name = wtypes.text
    description = wtypes.text
    image_id = wtypes.text


class OvercloudCategoryCount(Base):
    """Transfer object for overcloud category counts."""

    _db_class = db_models.OvercloudCategoryCount

    id = int
    resource_category_id = int
    overcloud_id = int
    num_nodes = int


class Overcloud(Base):
    """Transfer object for overclouds."""

    _db_class = db_models.Overcloud

    id = int
    stack_id = wtypes.text
    name = wtypes.text
    description = wtypes.text
    attributes = {wtypes.text: wtypes.text}
    counts = [OvercloudCategoryCount]

    @classmethod
    def from_db_model(cls, db_overcloud, skip_fields=None):
        # General Data
        transfer_overcloud = super(Overcloud, cls)\
            .from_db_model(db_overcloud, skip_fields=['attributes', 'counts'])

        # Attributes
        translated = {}
        for db_attribute in db_overcloud.attributes:
            translated[db_attribute.key] = db_attribute.value
        transfer_overcloud.attributes = translated

        # Counts
        transfer_overcloud.counts = [OvercloudCategoryCount.from_db_model(c)
                                     for c in db_overcloud.counts]
        return transfer_overcloud

    def to_db_model(self, omit_unset=False, skip_fields=None):
        # General Data
        db_model = super(Overcloud, self).to_db_model(
            omit_unset=omit_unset,
            skip_fields=['attributes', 'counts'])

        # Attributes
        if self.attributes != wtypes.Unset:

            translated = []
            for key, value in self.attributes.items():
                translated.append(db_models.OvercloudAttribute(
                    key=key, value=value, overcloud_id=self.id
                ))
            db_model.attributes = translated

        # Counts
        if self.counts != wtypes.Unset:
            db_model.counts = [c.to_db_model() for c in self.counts]

        return db_model
