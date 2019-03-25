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

from sawtooth_sdk.processor.exceptions import InvalidTransaction

from marketplace_processor.offer.accept_calc import AcceptOfferCalculator
from marketplace_processor.protobuf import offer_pb2
from marketplace_processor.protobuf import rule_pb2


def handle_accept_offer(accept_offer, header, state):
    """Handle Offer acceptance.

    Args:
        accept_offer (AcceptOffer): The transaction.
        header (TransactionHeader): The TransactionHeader.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        - InvalidTransaction
            - The Offer does not exist or is not Open
            - The receiver source Asset does not exist.
            - The receiver target Asset does not exist.
            - The offerer source asset resource does not match the
              receiver target asset resource.
            - The offerer target asset resource does not match the
              the receiver source asset resource.
            - The receiver source asset does not have the required quantity.
            - The offerer source asset does not have the required quantity.
    """

    offer = state.get_offer(identifier=accept_offer.id)

    check_validity_of_offer(offer, accept_offer)

    offer_accept = OfferAcceptance(offer, accept_offer, header, state)

    offer_accept.validate_exchange_once()

    offer_accept.validate_once_per_account()
    offer_accept.validate_accounts_limited_to()

    # The asset ids referernce Assets.
    offer_accept.validate_output_asset_exists()

    offer_accept.validate_input_asset_exists()

    # The resources match for the Assets
    offer_accept.validate_input_asset_resources()

    offer_accept.validate_output_asset_resources()

    calculator = AcceptOfferCalculator(offer=offer, count=accept_offer.count)

    # There is enough in each Asset to make the transaction.
    offer_accept.validate_output_enough(calculator.output_quantity())

    offer_accept.validate_input_enough(calculator.input_quantity())

    # Handle incrementing and decrementing the Assets' quantity
    offer_accept.handle_offerer_source(calculator.input_quantity())
    offer_accept.handle_offerer_target(calculator.output_quantity())
    offer_accept.handle_receiver_source(calculator.output_quantity())
    offer_accept.handle_receiver_target(calculator.input_quantity())

    offer_accept.handle_once_per_account()
    offer_accept.handle_exchange_once()


def check_validity_of_offer(offer, accept_offer):
    """Checks that the offer exists and is open.

    Args:
        offer (offer_pb2.Offer): The offer.
        accept_offer (AcceptOffer): The AcceptOffer txn.

    Raises:
        - InvalidTransaction
    """

    if not offer:
        raise InvalidTransaction(
            "Failed to accept Offer, Offer {} does not exist".format(
                accept_offer.id))
    if not offer.status == offer_pb2.Offer.OPEN:
        raise InvalidTransaction(
            "Failed to accept Offer, Offer {} is not open".format(
                accept_offer.id))


class OfferAcceptance(object):

    def __init__(self, offer, accept_offer, header, state):
        self._offer = offer
        self._accept_offer = accept_offer
        self._header = header

        self._state = state

        source_hldng = state.get_asset(offer.source)
        target_hldng = state.get_asset(
            offer.target) if offer.target else None
        resource = state.get_resource(target_hldng.resource) if target_hldng else None

        self._offerer = _OfferParticipant(
            source=source_hldng,
            target=target_hldng,
            source_resource=state.get_resource(source_hldng.resource),
            target_resource=resource)

        source = state.get_asset(accept_offer.source) \
            if accept_offer.source else None
        src_resource = state.get_resource(
            source.resource) if source else None
        target = state.get_asset(accept_offer.target)

        self._receiver = _OfferParticipant(
            source=source,
            source_resource=src_resource,
            target=target,
            target_resource=state.get_resource(target.resource))

    def validate_output_asset_exists(self):
        if self._offer.target and self._accept_offer.source:
            if self._offerer.target and not self._receiver.source:
                raise InvalidTransaction(
                    "Failed to accept offer, asset specified as source,{},"
                    " does not exist.".format(self._accept_offer.source))

    def validate_input_asset_exists(self):
        if not self._receiver.target:
            raise InvalidTransaction(
                "Failed to accept offer, asset specified as target, {},"
                " does not exist".format(self._accept_offer.target))

    def validate_input_asset_resources(self):
        if not self._offerer.source.resource == self._receiver.target.resource:
            raise InvalidTransaction(
                "Failed to accept offer, expected Asset resource {}, got "
                "resource {}".format(self._offerer.source.resource,
                                  self._receiver.target.resource))

    def validate_output_asset_resources(self):
        if self._offer.target \
                and self._offerer.target \
                and not \
                self._offerer.target.resource == self._receiver.source.resource:
            raise InvalidTransaction(
                "Failed to accept offer, expected Asset resource {}, got "
                "resource {}.".format(self._offerer.target.resource,
                                   self._receiver.source.resource))

    def validate_output_enough(self, output_quantity):
        if self._accept_offer.source and not _asset_is_infinite(
                self._receiver.source_resource,
                self._receiver.source.account) and \
                output_quantity > self._receiver.source.quantity:
            raise InvalidTransaction(
                "Failed to accept offer, needed quantity {}, but only had {} "
                "of {}".format(output_quantity,
                               self._receiver.source.quantity,
                               self._receiver.source.resource))

    def validate_input_enough(self, input_quantity):
        if not _asset_is_infinite(self._offerer.source_resource,
                                    self._offerer.source.account) and \
                input_quantity > self._offerer.source.quantity:
            raise InvalidTransaction(
                "Failed to accept offer, needed quantity {}, but only had {} "
                "of {}".format(input_quantity,
                               self._offerer.source.quantity,
                               self._offerer.source.resource))

    def validate_once_per_account(self):
        if _exchange_once_per_account(self._offer):
            if self._state.get_offer_account_receipt(
                    offer_id=self._offer.id,
                    account=self._header.signer_public_key):
                raise InvalidTransaction(
                    "Failed to accept offer, EXCHANGE ONCE PER ACCOUNT set "
                    "and account {} already has "
                    "accepted offer.".format(self._header.signer_public_key))

    def validate_exchange_once(self):
        if _exchange_once(self._offer):
            if self._state.offer_has_receipt(offer_id=self._offer.id):
                raise InvalidTransaction(
                    "Failed to accept offer, offer has already been accepted "
                    "and EXCHANGE ONCE is set.")

    def validate_accounts_limited_to(self):
        if _accounts_limited_to(self._offer):
            if self._header.signer_public_key not in _accounts(self._offer):
                raise InvalidTransaction(
                    "Failed to accept offer, accounts limited to {} but "
                    "account is {}".format(
                        _accounts(self._offer),
                        self._header.signer_public_key))

    def handle_offerer_source(self, input_quantity):
        if not _asset_is_infinite(self._offerer.source_resource,
                                    self._offerer.source.account):
            self._state.change_asset_quantity(
                self._offerer.source.id,
                self._offerer.source.quantity - input_quantity)

    def handle_offerer_target(self, output_quantity):
        if self._offer.target:
            self._state.change_asset_quantity(
                self._offerer.target.id,
                self._offerer.target.quantity + output_quantity)

    def handle_receiver_source(self, output_quantity):
        if self._accept_offer.source and not _asset_is_infinite(
                self._receiver.source_resource,
                self._receiver.source.account):
            self._state.change_asset_quantity(
                self._receiver.source.id,
                self._receiver.source.quantity - output_quantity)

    def handle_receiver_target(self, input_quantity):
        self._state.change_asset_quantity(
            self._receiver.target.id,
            self._receiver.target.quantity + input_quantity)

    def handle_once_per_account(self):
        if _exchange_once_per_account(self._offer):
            self._state.save_offer_account_receipt(
                offer_id=self._offer.id,
                account=self._header.signer_public_key)

    def handle_exchange_once(self):
        if _exchange_once(self._offer):
            self._state.save_offer_receipt(offer_id=self._offer.id)


def _has_rule(rules, rule_type):
    for rule in rules:
        if rule.type == rule_type:
            return True
    return False


def _accounts_limited_to(offer):
    if _has_rule(offer.rules, rule_pb2.Rule.EXCHANGE_LIMITED_TO_ACCOUNTS):
        return True
    return False


def _accounts(offer):
    return set.intersection(
        *[set(str(rule.value, 'utf-8').split(','))
          for rule in offer.rules
          if rule.type == rule_pb2.Rule.EXCHANGE_LIMITED_TO_ACCOUNTS])


def _exchange_once(offer):
    if _has_rule(offer.rules, rule_pb2.Rule.EXCHANGE_ONCE):
        return True
    return False


def _exchange_once_per_account(offer):
    if _has_rule(offer.rules, rule_pb2.Rule.EXCHANGE_ONCE_PER_ACCOUNT):
        return True
    return False


def _asset_is_infinite(resource, owner):
    if resource and (_has_rule(
            resource.rules,
            rule_pb2.Rule.ALL_ASSETS_INFINITE) or
                  _has_rule(
                      resource.rules,
                      rule_pb2.Rule.OWNER_ASSETS_INFINITE) and
                  owner in resource.owners):
        return True
    return False


class _OfferParticipant(object):

    def __init__(self, source, target, source_resource, target_resource):
        """Constructor.

        Args:
            source (Asset): The source Asset.
            target (Asset): The target Asset.
            source_resource (Resource): The source Resource.
            target_resource (Resource): The target Resource.
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
