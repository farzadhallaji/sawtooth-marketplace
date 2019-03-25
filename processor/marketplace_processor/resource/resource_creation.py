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


def handle_resource_creation(create_resource, header, state):
    """Handles creating an Resource.

    Args:
        create_resource (CreateResource): The transaction.
        header (TransactionHeader): The header of the Transaction.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        InvalidTransaction
            - The name already exists for an Resource.
            - The txn signer has an account
    """

    if not state.get_account(public_key=header.signer_public_key):
        raise InvalidTransaction(
            "Unable to create resource, signing key has no"
            " Account: {}".format(header.signer_public_key))

    if state.get_resource(name=create_resource.name):
        raise InvalidTransaction(
            "Resource already exists with Name {}".format(create_resource.name))

    state.set_resource(
        name=create_resource.name,
        description=create_resource.description,
        owners=[header.signer_public_key],
        rules=create_resource.rules)
