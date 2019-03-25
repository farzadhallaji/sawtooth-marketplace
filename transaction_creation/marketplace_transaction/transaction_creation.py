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

from marketplace_addressing import addresser

from marketplace_transaction.common import make_header_and_batch
from marketplace_transaction.protobuf import payload_pb2


def create_account(txn_key, batch_key, label, description):
    """Create a CreateAccount txn and wrap it in a batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The Txn signer key pair.
        batch_key (sawtooth_signing.Signer): The Batch signer key pair.
        label (str): The account's label.
        description (str): The description of the account.

    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [addresser.make_account_address(
        account_id=txn_key.get_public_key().as_hex())]

    outputs = [addresser.make_account_address(
        account_id=txn_key.get_public_key().as_hex())]

    account = payload_pb2.CreateAccount(
        label=label,
        description=description)
    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.CREATE_ACCOUNT,
        create_account=account)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


def create_resource(txn_key, batch_key, name, description, rules):
    """Create a CreateResource txn and wrap it in a batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The txn signer key pair.
        batch_key (sawtooth_signing.Signer): The batch signer key pair.
        name (str): The name of the resource.
        description (str): A description of the resource.
        rules (list): List of protobuf.rule_pb2.Rule

    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [addresser.make_resource_address(resource_id=name),
              addresser.make_account_address(
                  account_id=txn_key.get_public_key().as_hex())]

    outputs = [addresser.make_resource_address(resource_id=name)]

    resource = payload_pb2.CreateResource(
        name=name,
        description=description,
        rules=rules
    )

    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.CREATE_RESOURCE,
        create_resource=resource)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


def create_asset(txn_key,
                   batch_key,
                   identifier,
                   label,
                   description,
                   resource,
                   quantity):
    """Create a CreateAsset txn and wrap it in a batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The txn signer key pair.
        batch_key (sawtooth_signing.Signer): The batch signer key pair.
        identifier (str): The identifier of the Asset.
        label (str): The label of the Asset.
        description (str): The description of the Asset.
        quantity (int): The amount of the Resource.

    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [
        addresser.make_account_address(
            account_id=txn_key.get_public_key().as_hex()),
        addresser.make_resource_address(resource_id=resource),
        addresser.make_asset_address(asset_id=identifier)
    ]

    outputs = [addresser.make_asset_address(asset_id=identifier),
               addresser.make_account_address(
                   account_id=txn_key.get_public_key().as_hex())]

    asset_txn = payload_pb2.CreateAsset(
        id=identifier,
        label=label,
        description=description,
        resource=resource,
        quantity=quantity)

    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.CREATE_ASSET,
        create_asset=asset_txn)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


def create_offer(txn_key,
                 batch_key,
                 identifier,
                 label,
                 description,
                 source,
                 target,
                 rules):
    """Create a CreateOffer txn and wrap it in a batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The Txn signer key pair.
        batch_key (sawtooth_signing.Signer): The Batch signer key pair.
        identifier (str): The identifier of the Offer.
        label (str): The offer's label.
        description (str): The description of the offer.
        source (MarketplaceAsset): The asset id, quantity, resource to be
            drawn from.
        target (MarketplaceAsset): The asset id, quantity, resource to be
            paid into.
        rules (list): List of protobuf.rule_pb2.Rule


    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [
        addresser.make_account_address(
            account_id=txn_key.get_public_key().as_hex()),
        addresser.make_asset_address(
            asset_id=source.asset_id),
        addresser.make_offer_address(offer_id=identifier),
        addresser.make_resource_address(resource_id=source.resource)
    ]
    if target.asset_id:
        inputs.append(addresser.make_asset_address(
            asset_id=target.asset_id))
        inputs.append(addresser.make_resource_address(target.resource))

    outputs = [addresser.make_offer_address(offer_id=identifier)]

    offer_txn = payload_pb2.CreateOffer(
        id=identifier,
        label=label,
        description=description,
        source=source.asset_id,
        source_quantity=source.quantity,
        target=target.asset_id,
        target_quantity=target.quantity,
        rules=rules)

    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.CREATE_OFFER,
        create_offer=offer_txn)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


def accept_offer(txn_key,
                 batch_key,
                 identifier,
                 offerer,
                 receiver,
                 count):
    """Create an AcceptOffer txn and wrap it in a Batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The Txn signer key pair.
        batch_key (sawtooth_signing.Signer): The Batch signer key pair.
        identifier (str): The identifier of the Offer.
        offerer (OfferParticipant): The participant who made the offer.
        receiver (OfferParticipant): The participant who is accepting
            the offer.
        count (int): The number of units of exchange.

    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [addresser.make_asset_address(receiver.target),
              addresser.make_asset_address(offerer.source),
              addresser.make_resource_address(receiver.target_resource),
              addresser.make_resource_address(offerer.source_resource),
              addresser.make_offer_history_address(offer_id=identifier),
              addresser.make_offer_account_address(
                  offer_id=identifier,
                  account=txn_key.get_public_key().as_hex()),
              addresser.make_offer_address(identifier)]

    outputs = [addresser.make_asset_address(receiver.target),
               addresser.make_asset_address(offerer.source),
               addresser.make_offer_history_address(offer_id=identifier),
               addresser.make_offer_account_address(
                   offer_id=identifier,
                   account=txn_key.get_public_key().as_hex())]

    if receiver.source is not None:
        inputs.append(addresser.make_asset_address(receiver.source))
        inputs.append(addresser.make_resource_address(receiver.source_resource))
        outputs.append(addresser.make_asset_address(receiver.source))

    if offerer.target is not None:
        inputs.append(addresser.make_asset_address(offerer.target))
        inputs.append(addresser.make_resource_address(offerer.target_resource))
        outputs.append(addresser.make_asset_address(offerer.target))

    accept_txn = payload_pb2.AcceptOffer(
        id=identifier,
        source=receiver.source,
        target=receiver.target,
        count=count)

    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.ACCEPT_OFFER,
        accept_offer=accept_txn)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


def close_offer(txn_key, batch_key, identifier):
    """Create a CloseOffer txn and wrap it in a Batch and list.

    Args:
        txn_key (sawtooth_signing.Signer): The Txn signer key pair.
        batch_key (sawtooth_signing.Signer): The Batch signer key pair.
        identifier (str): The Offer identifier.

    Returns:
        tuple: List of Batch, signature tuple
    """

    inputs = [addresser.make_offer_address(identifier)]

    outputs = [addresser.make_offer_address(identifier)]

    close_txn = payload_pb2.CloseOffer(id=identifier)

    payload = payload_pb2.TransactionPayload(
        payload_type=payload_pb2.TransactionPayload.CLOSE_OFFER,
        close_offer=close_txn)

    return make_header_and_batch(
        payload=payload,
        inputs=inputs,
        outputs=outputs,
        txn_key=txn_key,
        batch_key=batch_key)


class OfferParticipant(object):

    def __init__(self, source, target, source_resource, target_resource):
        """Constructor

        Args:
            source (str): The id of the source Asset.
            target (str): The id of the target Asset.
            source_resource (str): The id of the source Resource.
            target_resource (str): The id of the target Resource.
        """

        self._source = source
        self._source_resource = source_resource

        self._target = target
        self._target_resource = target_resource

    @property
    def source(self):
        return self._source

    @property
    def source_resource(self):
        return self._source_resource

    @property
    def target(self):
        return self._target

    @property
    def target_resource(self):
        return self._target_resource


class MarketplaceAsset(object):

    def __init__(self, asset_id, quantity, resource):
        self._asset_id = asset_id
        self._quantity = quantity
        self._resource = resource

    @property
    def asset_id(self):
        return self._asset_id

    @property
    def quantity(self):
        return self._quantity

    @property
    def resource(self):
        return self._resource
