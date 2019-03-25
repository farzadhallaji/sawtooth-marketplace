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
# ------------------------------------------------------------------------------

from uuid import uuid4

from sanic import Blueprint
from sanic import response

from api import common
from api import messaging
from api.authorization import authorized

from marketplace_transaction import transaction_creation


ASSETS_BP = Blueprint('assets')


@ASSETS_BP.post('assets')
@authorized()
async def create_asset(request):
    """Creates a new Asset for the authorized Account"""
    required_fields = ['resource']
    common.validate_fields(required_fields, request.json)

    asset = _create_asset_dict(request)
    signer = await common.get_signer(request)

    batches, batch_id = transaction_creation.create_asset(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        identifier=asset['id'],
        label=asset.get('label'),
        description=asset.get('description'),
        resource=asset['resource'],
        quantity=asset['quantity'])

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    return response.json(asset)


def _create_asset_dict(request):
    keys = ['label', 'description', 'resource', 'quantity']
    body = request.json

    asset = {k: body[k] for k in keys if body.get(k) is not None}

    if asset.get('quantity') is None:
        asset['quantity'] = 0

    asset['id'] = str(uuid4())

    return asset
