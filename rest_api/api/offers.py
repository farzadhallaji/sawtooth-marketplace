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

import asyncio
from uuid import uuid4

from sanic import response
from sanic import Blueprint

from api.authorization import authorized
from api import common
from api import messaging
from api.errors import ApiBadRequest

from db import offers_query
from db.common import fetch_assets

from marketplace_transaction import transaction_creation


OFFERS_BP = Blueprint('offers')


@OFFERS_BP.post('offers')
@authorized()
async def create_offer(request):
    """Creates a new Offer in state"""
    required_fields = ['source', 'sourceQuantity']
    common.validate_fields(required_fields, request.json)

    signer = await common.get_signer(request)

    await asyncio.sleep(2.0)  # Mitigate race condition
    offer = _create_offer_dict(request.json, signer.get_public_key().as_hex())

    offer_assets = await _create_assets_dict(
        request.app.config.DB_CONN, offer)

    source, target = _create_marketplace_assets(offer, offer_assets)

    batches, batch_id = transaction_creation.create_offer(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        identifier=offer['id'],
        label=offer.get('label'),
        description=offer.get('description'),
        source=source,
        target=target,
        rules=offer.get('rules'))

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    if offer.get('rules'):
        offer['rules'] = request.json['rules']

    return response.json(offer)


@OFFERS_BP.get('offers')
async def get_all_offers(request):
    """Fetches complete details of all Offers in state"""
    keys = ['status', 'source', 'target']
    query_params = {
        k: request.args[k][0] for k in keys if request.args.get(k) is not None
    }
    offer_resources = await offers_query.fetch_all_offer_resources(
        request.app.config.DB_CONN, query_params)
    return response.json(offer_resources)


@OFFERS_BP.get('offers/<offer_id>')
async def get_offer(request, offer_id):
    """Fetches the details of particular Offer in state"""
    offer_resource = await offers_query.fetch_offer_resource(
        request.app.config.DB_CONN, offer_id)
    return response.json(offer_resource)


@OFFERS_BP.patch('offers/<offer_id>/accept')
@authorized()
async def accept_offer(request, offer_id):
    """Request for authorized Account to accept Offer"""
    required_fields = ['count', 'target']
    common.validate_fields(required_fields, request.json)

    offer = await offers_query.fetch_offer_resource(
        request.app.config.DB_CONN, offer_id)

    offer_assets = await _create_assets_dict(
        request.app.config.DB_CONN, offer)

    offerer, receiver = _create_offer_participants(
        request.json, offer, offer_assets)

    signer = await common.get_signer(request)
    batches, batch_id = transaction_creation.accept_offer(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        identifier=offer_id,
        offerer=offerer,
        receiver=receiver,
        count=request.json['count'])

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    return response.json('')


@OFFERS_BP.patch('offers/<offer_id>/close')
@authorized()
async def close_offer(request, offer_id):
    """Request by owner of Offer to close it"""
    signer = await common.get_signer(request)
    batches, batch_id = transaction_creation.close_offer(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        identifier=offer_id)

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    return response.json('')


def _create_marketplace_assets(offer, offer_assets):
    source = transaction_creation.MarketplaceAsset(
        asset_id=offer['source'],
        quantity=offer['sourceQuantity'],
        resource=offer_assets['source']['resource'])

    if offer.get('target'):
        target_resource = offer_assets['target']['resource']
    else:
        target_resource = None
    target = transaction_creation.MarketplaceAsset(
        asset_id=offer.get('target'),
        quantity=offer.get('targetQuantity'),
        resource=target_resource)

    return (source, target)


def _create_offer_participants(body, offer, offer_assets):
    input_resource = offer_assets['source']['resource']
    if offer.get('target'):
        output_resource = offer_assets['target']['resource']
    else:
        output_resource = None

    offerer = transaction_creation.OfferParticipant(
        source=offer['source'],
        target=offer.get('target'),
        source_resource=input_resource,
        target_resource=output_resource)

    receiver = transaction_creation.OfferParticipant(
        source=body.get('source'),
        target=body['target'],
        source_resource=output_resource,
        target_resource=input_resource)

    return (offerer, receiver)


async def _create_assets_dict(conn, asset_ids):
    keys = ['source', 'target']
    assets = await fetch_assets([
        asset_ids.get(k) for k in keys if asset_ids.get(k) is not None
    ]).run(conn)

    assets_dict = {
        k: h for h in assets for k in keys if asset_ids.get(k) == h['id']
    }

    return assets_dict


def _create_offer_dict(body, public_key):
    keys = ['label', 'description', 'source', 'target',
            'sourceQuantity', 'targetQuantity']

    offer = {k: body[k] for k in keys if body.get(k) is not None}

    if offer['sourceQuantity'] < 1:
        raise ApiBadRequest("sourceQuantity must be a positive integer")
    if offer.get('targetQuantity') and offer['targetQuantity'] < 1:
        raise ApiBadRequest("targetQuantity must be a positive integer")

    offer['id'] = str(uuid4())
    offer['owners'] = [public_key]
    offer['status'] = "OPEN"

    if body.get('rules'):
        offer['rules'] = common.proto_wrap_rules(body['rules'])

    return offer
