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
const api = require('../services/api')
const layout = require('../components/layout')
const mkt = require('../components/marketplace')
const { acceptOffer } = require('./accept_offer_modal')

const filterDropdown = (label, resources, setter) => {
  const options = resources.map(resource => ({
    text: resource,
    onclick: setter(resource)
  }))
  options.push({
    text: m('em', 'clear filter'),
    onclick: setter(null)
  })

  return layout.dropdown(label, options, 'success')
}

const acceptButton = (offer, account = null) => {
  const onclick = () => acceptOffer(offer.id)
  let disabled = false
  if (!account) disabled = true
  else if (offer.targetQuantity === 0) disabled = false
  else if (!account.quantities[offer.targetResource]) disabled = true
  else if (account.quantities[offer.targetResource] < offer.targetQuantity) {
    disabled = true
  }

  return m(
    `button.btn.btn-lg.btn-outline-${disabled ? 'secondary' : 'primary'}`,
    { onclick, disabled },
    'Accept')
}

const offerRow = account => offer => {
  return [
    m('.row.my-2',
      m('.col-md-9',
        m('a.h5', {
          href: `/offers/${offer.id}`,
          oncreate: m.route.link
        }, offer.label || offer.id)),
      m('.col-md-3.text-right', acceptButton(offer, account))),
    mkt.bifold({
      header: offer.sourceResource,
      body: offer.sourceQuantity
    }, {
      header: offer.targetResource,
      body: offer.targetQuantity || 'free'
    })
  ]
}

const pluckUniq = (items, key) => _.uniq(items.map(item => item[key]))

/**
 * A page displaying each Resource, with links to create an Offer,
 * or to view more detail.
 */
const OfferListPage = {
  oninit (vnode) {
    Promise.all([api.get('offers'), api.get('accounts')])
      .then(([ offers, accounts ]) => {
        // Pair each asset with its resource type
        const assetResources = _.chain(accounts)
          .map(account => account.assets)
          .flatten()
          .reduce((assetResources, asset) => {
            assetResources[asset.id] = asset.resource
            return assetResources
          }, {})
          .value()

        // Save offers to state with resource names
        vnode.state.offers = offers.map(offer => {
          return _.assign({
            sourceResource: assetResources[offer.source],
            targetResource: assetResources[offer.target]
          }, offer)
        })

        // If logged in, save account to state with resource quantities
        const publicKey = api.getPublicKey()
        if (publicKey) {
          const account = accounts
            .find(account => account.publicKey === publicKey)

          const quantities = acct.getResourceQuantities(account)
          vnode.state.account = _.assign({ quantities }, account)
        }
      })
      .catch(api.ignoreError)
  },

  view (vnode) {
    let offers = _.get(vnode.state, 'offers', [])
    const sourceResources = pluckUniq(offers, 'sourceResource')
    const targetResources = pluckUniq(offers, 'targetResource')

    if (vnode.state.source) {
      offers = offers.filter(offer => {
        return offer.sourceResource === vnode.state.source
      })
    }

    if (vnode.state.target) {
      offers = offers.filter(offer => {
        return offer.targetResource === vnode.state.target
      })
    }

    return [
      layout.title('Available Offers'),
      m('.container',
        m('.row.text-center.my-4',
          m('.col-md-5',
            filterDropdown(
              vnode.state.source || 'Offered',
              sourceResources,
              resource => () => { vnode.state.source = resource })),
          m('.col-md-2'),
          m('.col-md-5',
            filterDropdown(
              vnode.state.target || 'Requested',
              targetResources,
              resource => () => { vnode.state.target = resource }))),
        offers.length > 0
          ? offers.map(offerRow(vnode.state.account))
          : m('.text-center.font-italic',
              'there are currently no available offers'))
    ]
  }
}

module.exports = OfferListPage
