/**
 * Copyright 2017 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ----------------------------------------------------------------------------
 */
'use strict'

const m = require('mithril')
const _ = require('lodash')

const acct = require('../services/account')
const layout = require('../components/layout')
const api = require('../services/api')
const { createOffer } = require('./create_offer_modal')

const offerButton = (name, disabled, key = 'source') => {
  const label = key === 'target' ? 'Request' : 'Offer'
  const onclick = key === 'target'
    ? () => createOffer(null, name)
    : () => createOffer(name)

  return m(`button.btn.btn-outline-${disabled ? 'secondary' : 'primary'}.mr-3`,
           { onclick, disabled },
           label)
}

const resourceRowMapper = account => resource => {
  const safeName = window.encodeURI(resource.name)
  const offerDisabled = !account ||
    !account.quantities[resource.name] ||
    (resource.rules.find(({ type }) => type === 'NOT_TRANSFERABLE') &&
      !resource.owners.find(owner => owner === account.publicKey))
  const requestDisabled = !account

  return m('.row.mb-5', [
    m('.col-md-8', [
      layout.row(m('a.h5', {
        href: `/resources/${safeName}`,
        oncreate: m.route.link
      }, resource.name)),
      layout.row(m('.text-muted', resource.description))
    ]),
    m('.col-md-4.mt-3', [
      offerButton(resource.name, offerDisabled),
      offerButton(resource.name, requestDisabled, 'target')
    ])
  ])
}

/**
 * A page displaying each Resource, with links to create an Offer,
 * or to view more detail.
 */
const ResourceListPage = {
  oninit (vnode) {
    Promise.all([ acct.getUserAccount(), api.get(`resources`) ])
      .then(([ account, resources ]) => {
        vnode.state.resources = resources

        if (account) {
          const quantities = acct.getResourceQuantities(account)
          vnode.state.account = _.assign({ quantities }, account)
        }
      })
      .catch(api.ignoreError)
  },

  view (vnode) {
    const resources = _.get(vnode.state, 'resources', [])

    return [
      layout.title('Resources Available'),
      m('.container.mt-6',
        resources.length > 0
          ? resources.map(resourceRowMapper(vnode.state.account))
          : m('.text-center',
              m('em', 'there are currently no available resources')))
    ]
  }
}

module.exports = ResourceListPage
