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
from marketplace_processor.protobuf import account_pb2
from marketplace_processor.protobuf import resource_pb2
from marketplace_processor.protobuf import asset_pb2
from marketplace_processor.protobuf import offer_pb2
from marketplace_processor.protobuf import transfer_pb2
from marketplace_processor.protobuf import offer_history_pb2
from marketplace_processor.protobuf import rule_pb2


OFFER_RULES = [rule_pb2.Rule.EXCHANGE_ONCE_PER_ACCOUNT,
               rule_pb2.Rule.EXCHANGE_ONCE,
               rule_pb2.Rule.EXCHANGE_LIMITED_TO_ACCOUNTS]


class MarketplaceState(object):

    def __init__(self, context, timeout=2):
        self._context = context
        self._timeout = timeout
        self._state_entries = []

    def get_transfer(self, identifier , account):
        address = addresser.make_transfer_address(transfer_id=identifier, account = account)
        print("address ========= state ===========> " , address)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))       
        
        print("_context.get_state ========= state ===========> " , self._context.get_state(addresses=[address],timeout=self._timeout))
        print("self._get_transfer ========= state ===========> " , self._get_transfer(address=address, identifier=identifier))

        return self._get_transfer(address=address, identifier=identifier)

    def _get_transfer(self, address, identifier):

        container = _get_transfer_container(self._state_entries, address)
        transfer = None
        try:
            transfer = _get_transfer_from_container(container, identifier)
        except KeyError:
            # We are fine with returning None
            pass

        return transfer

    def get_offer(self, identifier):
        address = addresser.make_offer_address(offer_id=identifier)
        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        return self._get_offer(address=address, identifier=identifier)

    def _get_offer(self, address, identifier):

        container = _get_offer_container(self._state_entries, address)
        offer = None
        try:
            offer = _get_offer_from_container(container, identifier)
        except KeyError:
            # We are fine with returning None
            pass

        return offer

    def set_create_offer(self,
                         identifier,
                         label,
                         description,
                         owners,
                         source,
                         source_quantity,
                         target,
                         target_quantity,
                         rules):
        address = addresser.make_offer_address(offer_id=identifier)
        container = _get_offer_container(self._state_entries, address)

        try:
            offer = _get_offer_from_container(container, identifier)

        except KeyError:
            offer = container.entries.add()

        offer.id = identifier
        offer.label = label
        offer.description = description
        offer.owners.extend(owners)
        offer.source = source
        offer.source_quantity = source_quantity
        offer.target = target
        offer.target_quantity = target_quantity
        offer.rules.extend(rules)
        offer.status = offer_pb2.Offer.OPEN

        offer.rules.extend(self._return_offer_rules(source))
        if target:
            offer.rules.extend(self._return_offer_rules(target))

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def _return_offer_rules(self, asset_id,):
        asset_addr = addresser.make_asset_address(asset_id)
        asset = self._get_asset(asset_addr, asset_id)
        resource = self.get_resource(asset.resource)
        return [r for r in resource.rules if r.type in OFFER_RULES]

    def close_offer(self, identifier):
        address = addresser.make_offer_address(offer_id=identifier)
        container = _get_offer_container(self._state_entries, address)

        try:
            offer = _get_offer_from_container(container, identifier)

        except KeyError:
            offer = container.entries.add()

        offer.status = offer_pb2.Offer.CLOSED

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_asset(self, identifier):
        address = addresser.make_asset_address(asset_id=identifier)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        return self._get_asset(address=address, identifier=identifier)

    def _get_asset(self, address, identifier):

        container = _get_asset_container(self._state_entries, address)

        asset = None
        try:
            asset = _get_asset_from_container(container, identifier)
        except KeyError:
            # Fine with returning None
            pass
        return asset

    def set_asset(self,
                    identifier,
                    label,
                    description,
                    account,
                    resource,
                    quantity):
        address = addresser.make_asset_address(asset_id=identifier)
        container = _get_asset_container(self._state_entries, address)

        try:
            asset = _get_asset_from_container(container, identifier)
        except KeyError:
            asset = container.entries.add()

        asset.id = identifier
        asset.label = label
        asset.description = description
        asset.account = account
        asset.resource = resource
        asset.quantity = quantity

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def change_asset_quantity(self,
                                identifier,
                                new_quantity):
        address = addresser.make_asset_address(asset_id=identifier)
        container = _get_asset_container(self._state_entries, address)

        try:
            asset = _get_asset_from_container(container, identifier)
        except KeyError:
            asset = container.entries.add()

        asset.quantity = new_quantity

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()

        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_resource(self, name):
        address = addresser.make_resource_address(resource_id=name)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        return self._get_resource(address=address, name=name)

    def _get_resource(self, address, name):

        container = _get_resource_container(self._state_entries, address)

        resource = None
        try:
            resource = _get_resource_from_container(container, name)
        except KeyError:
            # We are fine with returning None for an resource that doesn't exist
            pass
        return resource

    def set_resource(self, name, description, owners, rules):
        address = addresser.make_resource_address(name)

        container = _get_resource_container(self._state_entries, address)

        try:
            resource = _get_resource_from_container(container, name)
        except KeyError:
            resource = container.entries.add()

        resource.name = name
        resource.description = description
        resource.owners.extend(owners)
        resource.rules.extend(rules)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_account(self, public_key):
        address = addresser.make_account_address(account_id=public_key)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_account_container(self._state_entries, address)
        account = None
        try:
            account = _get_account_from_container(
                container,
                identifier=public_key)
        except KeyError:
            # We are fine with returning None for an account that doesn't
            # exist in state.
            pass
        return account

    def set_account(self, public_key, label, description, assets):
        address = addresser.make_account_address(account_id=public_key)

        container = _get_account_container(self._state_entries, address)

        try:
            account = _get_account_from_container(
                container,
                public_key)
        except KeyError:
            account = container.entries.add()

        account.public_key = public_key
        account.label = label
        account.description = description
        for asset in assets:
            account.assets.append(asset)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def add_asset_to_account(self, public_key, asset_id):
        address = addresser.make_account_address(account_id=public_key)

        container = _get_account_container(self._state_entries, address)

        try:
            account = _get_account_from_container(
                container,
                public_key)
        except KeyError:
            account = container.entries.add()

        account.assets.append(asset_id)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def save_offer_account_receipt(self, offer_id, account):
        address = addresser.make_offer_account_address(
            offer_id=offer_id,
            account=account)

        container = _get_history_container(self._state_entries, address)
        offer_history = container.entries.add()

        offer_history.offer_id = offer_id
        offer_history.account_id = account

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def save_offer_receipt(self, offer_id):
        address = addresser.make_offer_history_address(offer_id=offer_id)

        container = _get_history_container(self._state_entries, address)
        offer_history = container.entries.add()

        offer_history.offer_id = offer_id

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def offer_has_receipt(self, offer_id):
        address = addresser.make_offer_history_address(
            offer_id=offer_id)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_history_container(self._state_entries, address)

        try:
            _get_history_by_offer_id(
                container,
                offer_id=offer_id)
            return True
        except KeyError:
            return False

    def get_offer_account_receipt(self, offer_id, account):
        address = addresser.make_offer_account_address(
            offer_id=offer_id,
            account=account)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_history_container(self._state_entries, address)
        offer_history = None
        try:
            offer_history = _get_history_from_container(
                container,
                offer_id=offer_id,
                account=account)
        except KeyError:
            # we are fine returning None
            pass

        return offer_history


def _get_history_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = offer_history_pb2.OfferHistoryContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = offer_history_pb2.OfferHistoryContainer()

    return container


def _get_history_by_offer_id(container, offer_id):
    for offer_history in container.entries:
        if offer_history.offer_id == offer_id:
            return offer_history
    raise KeyError("OfferHistory not found in container.")


def _get_history_from_container(container, offer_id, account):
    for offer_history in container.entries:
        if offer_history.offer_id == offer_id \
                and offer_history.account_id == account:
            return offer_history
    raise KeyError("OfferHistory not found in container.")


def _get_transfer_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = transfer_pb2.TransferContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = transfer_pb2.TransferContainer()

    return container

def _get_transfer_from_container(container, transfer_id):
    for transfer in container.entries:
        if transfer.id == transfer_id:
            return transfer
    raise KeyError(
        "Transfer with id {} is not in container".format(transfer_id))

def _get_offer_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = offer_pb2.OfferContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = offer_pb2.OfferContainer()

    return container


def _get_offer_from_container(container, offer_id):
    for offer in container.entries:
        if offer.id == offer_id:
            return offer
    raise KeyError(
        "Offer with id {} is not in container".format(offer_id))


def _get_asset_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = asset_pb2.AssetContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = asset_pb2.AssetContainer()

    return container


def _get_asset_from_container(container, asset_id):
    for asset in container.entries:
        if asset.id == asset_id:
            return asset
    raise KeyError(
        "Asset with id {} is not in container".format(asset_id))


def _get_resource_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = resource_pb2.ResourceContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = resource_pb2.ResourceContainer()
    return container


def _get_resource_from_container(container, name):
    for resource in container.entries:
        if resource.name == name:
            return resource
    raise KeyError(
        "Resource with name {} is not in container".format(name))


def _get_account_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = account_pb2.AccountContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = account_pb2.AccountContainer()

    return container


def _get_account_from_container(container, identifier):
    for account in container.entries:
        if account.public_key == identifier:
            return account
    raise KeyError(
        "Account with identifier {} is not in container.".format(identifier))


def _find_in_state(state_entries, address):
    for entry in state_entries:
        if entry.address == address:
            return entry
    raise KeyError("Address {} not found in state".format(address))
