# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from marketplace_processor.protobuf import payload_pb2


class MarketplacePayload(object):

    def __init__(self, payload):
        self._transaction = payload_pb2.TransactionPayload()
        self._transaction.ParseFromString(payload)

    def create_account(self):
        """Returns the value set in the create_account.

        Returns:
            payload_pb2.CreateAccount
        """

        return self._transaction.create_account

    def is_create_account(self):

        create_account = payload_pb2.TransactionPayload.CREATE_ACCOUNT

        return self._transaction.payload_type == create_account

    def create_asset(self):
        """Returns the value set in the create_asset.

        Returns:
            payload_pb2.CreateAsset
        """

        return self._transaction.create_asset

    def is_create_asset(self):

        create_asset = payload_pb2.TransactionPayload.CREATE_ASSET

        return self._transaction.payload_type == create_asset

    def create_resource(self):
        """Returns the value set in the create_resource.

        Returns:
            payload_pb2.CreateResource
        """

        return self._transaction.create_resource

    def is_create_resource(self):

        create_resource = payload_pb2.TransactionPayload.CREATE_RESOURCE

        return self._transaction.payload_type == create_resource

    def create_offer(self):
        """Returns the value set in the create_offer.

        Returns:
            payload_pb2.CreateOffer
        """

        return self._transaction.create_offer

    def is_create_offer(self):

        create_offer = payload_pb2.TransactionPayload.CREATE_OFFER

        return self._transaction.payload_type == create_offer

    def accept_offer(self):
        """Returns the value set in accept_offer.

        Returns:
            payload_pb2.AcceptOffer
        """

        return self._transaction.accept_offer

    def is_accept_offer(self):

        accept_offer = payload_pb2.TransactionPayload.ACCEPT_OFFER

        return self._transaction.payload_type == accept_offer

    def close_offer(self):
        """Returns the value set in close_offer.

        Returns:
            payload_pb2.CloseOffer
        """

        return self._transaction.close_offer

    def is_close_offer(self):

        close_offer = payload_pb2.TransactionPayload.CLOSE_OFFER

        return self._transaction.payload_type == close_offer


    def transfer_asset(self):
        """Returns the value set in transfer_asset.

        Returns:
            payload_pb2.AcceptOffer
        """

        return self._transaction.transfer_asset

    def is_transfer_asset(self):

        transfer_asset = payload_pb2.TransactionPayload.TRANSFER_ASSET

        return self._transaction.payload_type == transfer_asset
