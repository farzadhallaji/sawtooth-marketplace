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

import rethinkdb as re
from rethinkdb.errors import ReqlNonExistenceError

from api.errors import ApiBadRequest

from db.common import fetch_latest_block_num
from db.common import parse_rules


r=re.RethinkDB()

async def fetch_all_resource_resources(conn):
    return await r.table('resources')\
        .filter((fetch_latest_block_num() >= r.row['start_block_num'])
                & (fetch_latest_block_num() < r.row['end_block_num']))\
        .map(lambda resource: (resource['description'] == "").branch(
            resource.without('description'), resource))\
        .map(lambda resource: (resource['rules'] == []).branch(
            resource, resource.merge(parse_rules(resource['rules']))))\
        .without('start_block_num', 'end_block_num', 'delta_id')\
        .coerce_to('array').run(conn)


async def fetch_resource_resource(conn, name):
    try:
        return await r.table('resources')\
            .get_all(name, index='name')\
            .max('start_block_num')\
            .do(lambda resource: (resource['description'] == "").branch(
                resource.without('description'), resource))\
            .do(lambda resource: (resource['rules'] == []).branch(
                resource, resource.merge(parse_rules(resource['rules']))))\
            .without('start_block_num', 'end_block_num', 'delta_id')\
            .run(conn)
    except ReqlNonExistenceError:
        raise ApiBadRequest(
            "Bad Request: "
            "No resource with the name {} exists".format(name))
