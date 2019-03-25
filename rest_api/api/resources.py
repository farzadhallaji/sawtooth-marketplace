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

from urllib.parse import unquote

from sanic import Blueprint
from sanic import response

from api.authorization import authorized
from api import common
from api import messaging

from db import resources_query

from marketplace_transaction import transaction_creation


RESOURCES_BP = Blueprint('resources')


@RESOURCES_BP.post('resources')
@authorized()
async def create_resource(request):
    """Creates a new Resource in state"""
    required_fields = ['name']
    common.validate_fields(required_fields, request.json)

    signer = await common.get_signer(request)
    resource = _create_resource_dict(request.json, signer.get_public_key().as_hex())

    batches, batch_id = transaction_creation.create_resource(
        txn_key=signer,
        batch_key=request.app.config.SIGNER,
        name=resource.get('name'),
        description=resource.get('description'),
        rules=resource.get('rules'))

    await messaging.send(
        request.app.config.VAL_CONN,
        request.app.config.TIMEOUT,
        batches)

    await messaging.check_batch_status(request.app.config.VAL_CONN, batch_id)

    if resource.get('rules'):
        resource['rules'] = request.json['rules']

    return response.json(resource)


@RESOURCES_BP.get('resources')
async def get_all_resources(request):
    """Fetches complete details of all Resources in state"""
    resource_resources = await resources_query.fetch_all_resource_resources(
        request.app.config.DB_CONN)
    return response.json(resource_resources)


@RESOURCES_BP.get('resources/<name>')
async def get_resource(request, name):
    """Fetches the details of particular Resource in state"""
    decoded_name = unquote(name)
    resource_resource = await resources_query.fetch_resource_resource(
        request.app.config.DB_CONN, decoded_name)
    return response.json(resource_resource)


def _create_resource_dict(body, public_key):
    keys = ['name', 'description']

    resource = {k: body[k] for k in keys if body.get(k) is not None}
    resource['owners'] = [public_key]

    if body.get('rules'):
        resource['rules'] = common.proto_wrap_rules(body['rules'])

    return resource
