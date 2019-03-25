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

from marketplace_processor.protobuf import rule_pb2


def handle_offer_creation(create_offer, header, state):
    """Handle Offer creation.

    Args:
        create_offer (CreateOffer): The transaction.
        header (TransactionHeader): The header of the Transaction.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        InvalidTransaction
            - There is already an Offer with the same identifier.
            - The txn signer does not have an Account.
            - Either the source or target Asset account is not the signer.
            - The source is unset.
            - The source_quantity is unset or 0.
            - The target or target_quantity are set while the other is unset.
            - The source is not a asset.
            - THe target is not a asset.

    """

    if state.get_offer(identifier=create_offer.id):
        raise InvalidTransaction(
            "Failed to create Offer, id {} already exists.".format(
                create_offer.id))

    if not state.get_account(public_key=header.signer_public_key):
        raise InvalidTransaction(
            "Failed to create offer, transaction signer {} does "
            "not have an Account.".format(header.signer_public_key))

    if not create_offer.source:
        raise InvalidTransaction(
            "Failed to create Offer, Offer source is not specified.")

    if create_offer.source_quantity == 0:
        raise InvalidTransaction("Failed to create Offer, source_quantity "
                                 "was unset or 0")

    source_asset = state.get_asset(identifier=create_offer.source)
    if not source_asset:
        raise InvalidTransaction(
            "Failed to create Offer, Asset id {} listed as source "
            "does not refer to a Asset.".format(create_offer.source))

    if not source_asset.account == header.signer_public_key:
        raise InvalidTransaction(
            "Failed to create Offer, source Asset account {} not "
            "owned by txn signer {}".format(source_asset.account,
                                            header.signer_public_key))
    source_resource = state.get_resource(source_asset.resource)
    if _is_not_transferable(source_resource, header.signer_public_key):
        raise InvalidTransaction(
            "Failed to create Offer, source resource {} are not "
            "transferable".format(source_resource.name))

    if create_offer.target and not create_offer.target_quantity or \
            create_offer.target_quantity and not create_offer.target:
        raise InvalidTransaction("Failed to create Offer, target and "
                                 "target_quantity must both be set or "
                                 "both unset.")

    if create_offer.target:
        target_asset = state.get_asset(identifier=create_offer.target)
        if not target_asset:
            raise InvalidTransaction(
                "Failed to create Offer, Asset id {} listed as target "
                "does not refer to a Asset.".format(create_offer.target))

        if not target_asset.account == header.signer_public_key:
            raise InvalidTransaction(
                "Failed to create Offer, target Asset account {} not "
                "owned by txn signer {}".format(target_asset.account,
                                                header.signer_public_key))
        target_resource = state.get_resource(target_asset.resource)
        if _is_not_transferable(target_resource, header.signer_public_key):
            raise InvalidTransaction(
                "Failed to create Offer, target resource {} is not "
                "transferable".format(target_resource.name))

    state.set_create_offer(
        identifier=create_offer.id,
        label=create_offer.label,
        description=create_offer.description,
        owners=[header.signer_public_key],
        source=create_offer.source,
        source_quantity=create_offer.source_quantity,
        target=create_offer.target,
        target_quantity=create_offer.target_quantity,
        rules=create_offer.rules)


def _is_not_transferable(resource, owner_public_key):
    if _has_rule(resource.rules, rule_pb2.Rule.NOT_TRANSFERABLE) \
            and owner_public_key not in resource.owners:
        return True
    return False


def _has_rule(rules, rule_type):
    for rule in rules:
        if rule.type == rule_type:
            return True
    return False
