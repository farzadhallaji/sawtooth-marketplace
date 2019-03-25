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


def handle_asset_creation(create_asset, header, state):
    """

    Args:
        create_asset (CreateAsset): The transaction.
        header (TransactionHeader): The header of the Transaction.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        InvalidTransaction
            - There is already a Asset with the same identifier.
            - The txn signer does not own an Account.
            - The Resource does not exist.
            - The quantity is not 0 and the Resource owner doesn't match the
              transaction signer public key.
    """

    if state.get_asset(identifier=create_asset.id):
        raise InvalidTransaction("Failed to create Asset, id {} already "
                                 "exists.".format(create_asset.id))

    if not state.get_account(public_key=header.signer_public_key):
        raise InvalidTransaction(
            "Failed to create Asset, account {} does not exist.".format(
                header.signer_public_key))

    resource = state.get_resource(name=create_asset.resource)
    if not resource:
        raise InvalidTransaction(
            "Failed to create Asset, resource {} does not "
            "exist.".format(create_asset.resource))

    if create_asset.quantity > 0 and \
            header.signer_public_key not in resource.owners:
        raise InvalidTransaction(
            "Failed to create Asset, quantity {} is non-zero and the "
            "transaction signer public key {} is not an owner of "
            "the Resource {}".format(create_asset.quantity,
                                  header.signer_public_key,
                                  resource.name))

    state.set_asset(
        identifier=create_asset.id,
        label=create_asset.label,
        description=create_asset.description,
        account=header.signer_public_key,
        resource=create_asset.resource,
        quantity=create_asset.quantity)

    state.add_asset_to_account(
        public_key=header.signer_public_key,
        asset_id=create_asset.id)
