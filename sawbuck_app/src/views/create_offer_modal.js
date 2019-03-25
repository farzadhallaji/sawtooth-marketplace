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
const forms = require('../components/forms')
const layout = require('../components/layout')
const mkt = require('../components/marketplace')
const modals = require('../components/modals')

// Returns a label string, truncated if necessary
const getLabel = (value, defaultValue, max = 10) => {
  const label = value || defaultValue
  if (label.length <= max) return label
  return `${label.slice(0, max - 3)}...`
}

// Returns a green check mark if visible
const check = (isVisible = true) => {
  return m(`span.text-${isVisible ? 'success' : 'white'}`,
           layout.icon('check'),
           ' ')
}

// Filters assets by resource if set, sorting otherwise
const getAssets = (assets, resource = null) => {
  if (resource) {
    return assets.filter(asset => asset.resource === resource)
  }
  return _.sortBy(assets, ['resource', 'label'])
}

// Returns a functon which sets id and label keys for source
const sourceSetter = (state, key = 'source') => (id, resource) => () => {
  state.offer[key] = id
  state[`${key}Label`] = resource
}

// Returns a function which sets id, label, and additional keys for target
const targetSetter = state => (id, resource, isFree, isNew) => () => {
  sourceSetter(state, 'target')(id, resource)()
  state.noTarget = isFree
  state.hasNewAsset = isNew
}

// Gets a list of option objects, with text and an onclick function
const getOptions = (assets, state, key = 'source') => {
  const setter = key !== 'target' ? sourceSetter(state) : targetSetter(state)

  return assets.map(asset => ({
    text: [
      check(state.offer[key] === asset.id),
      `${asset.resource} (${asset.label || asset.id})`
    ],
    onclick: setter(asset.id, asset.resource)
  }))
}

// Returns two additional options, free and new asset
const optionsTail = state => {
  return [{
    text: [check(state.noTarget === true), m('em', 'free (No Asset)')],
    onclick: targetSetter(state)(null, 'free', true)
  }, {
    text: [check(state.hasNewAsset === true), m('em', 'new (New Asset)')],
    onclick: targetSetter(state)(null, 'new', false, true)
  }]
}

// A small dropdown for selecting an resource for a new asset
const resourceDropdown = (label, resources, onValue) => {
  return m('span.dropdown.ml-3', [
    m('button.btn.btn-success.btn-sm.dropdown-toggle.mb-1', {
      type: 'button',
      'data-toggle': 'dropdown',
      'aria-haspopup': 'true',
      'aria-expanded': 'false'
    }, label || 'Resource'),
    m('.dropdown-menu',
      resources.map(resource => {
        return m('button.dropdown-item', {
          type: 'button',
          onclick: () => onValue(resource.name)
        }, check(label === resource.name), resource.name)
      }))
  ])
}

// Small fields with placeholders rather than headers, for new assets
const assetField = (placeholder, onValue) => {
  return forms.field(onValue, { placeholder, required: false })
}

// A labeled checkbox that will set or unset a rule in state
const ruleCheckbox = (state, name, label) => {
  const path = ['asset', 'rules', name, 'isSet']
  return m('.form-check', [
    m('label.form-check-label',
      m('input.form-check-input', {
        type: 'checkbox',
        onclick: () => _.set(state, path, !_.get(state, path))
      }), label)
  ])
}

// Convert booleans and values in state to proper rule objects
const getRules = state => {
  const ruleObj = _.get(state, 'asset.rules', {})
  return _.reduce(ruleObj, (rules, rule, type) => {
    if (rule.isSet) {
      const newRule = { type }
      if (rule.keys) newRule.value = rule.keys.split(',')
      rules = rules.concat(newRule)
    }
    return rules
  }, [])
}

// Returns true or false depending on whether or not the form is valid
const isFormValid = state => {
  if (!state.offer.source) return false
  if (!state.offer.sourceQuantity) return false
  if (state.noTarget) return true

  if (!state.offer.targetQuantity) return false
  if (state.hasNewAsset && !state.asset.resource) return false
  if (!state.hasNewAsset && !state.offer.target) return false

  return true
}

// Returns a function which will submit a new offer, and asset if applicable
const submitter = (state, onDone) => () => {
  return Promise.resolve()
    .then(() => {
      if (state.hasNewAsset) {
        const assetKeys = ['label', 'description', 'resource']
        return api.post('assets', _.pick(state.asset, assetKeys))
      }
    })
    .then(asset => {
      const offerKeys = [
        'label', 'description', 'source', 'sourceQuantity',
        'target', 'targetQuantity'
      ]
      const offer = _.pick(state.offer, offerKeys)
      if (asset) offer.target = asset.id
      offer.rules = getRules(state)
      return api.post('offers', offer)
    })
    .then(onDone)
    .then(() => m.route.set('/offers'))
    .then(() => new Promise(resolve => setTimeout(resolve, 2000)))
    .then(() => window.location.reload())
    .catch(api.alertError)
}

// A versatile modal allowing users to create new offers (and new assets)
const CreateOfferModal = {
  oninit (vnode) {
    vnode.state.offer = {}
    vnode.state.asset = {}
    vnode.state.hasNewAsset = false

    return Promise.all([
      acct.getUserAccount(),
      vnode.attrs.target ? null : api.get('resources')
    ])
      .then(([ account, resources ]) => {
        if (!account) return vnode.attrs.cancelFn()
        if (resources && resources.error) return console.error(account.error)
        if (account.error) return console.error(account.error)
        vnode.state.resources = resources

        vnode.state.sources = getAssets(account.assets, vnode.attrs.source)
        vnode.state.targets = getAssets(account.assets, vnode.attrs.target)

        if (vnode.attrs.source) {
          vnode.state.sourceLabel = vnode.attrs.source
          vnode.state.offer.source = vnode.state.sources[0].id
        }

        if (vnode.attrs.target) {
          vnode.state.targetLabel = vnode.attrs.target
          vnode.state.offer.target = vnode.state.sources[0].id
        }
      })
  },

  view (vnode) {
    const resources = _.get(vnode.state, 'resources', [])
    const sources = _.get(vnode.state, 'sources', [])
    const targets = _.get(vnode.state, 'targets', [])
    const sourceOptions = getOptions(sources, vnode.state)
    const targetOptions = getOptions(targets, vnode.state, 'target')

    const setter = path => value => _.set(vnode.state, path, value)
    const intSetter = path => int => {
      _.set(vnode.state, path, window.parseInt(int))
    }

    if (!vnode.attrs.target) {
      Array.prototype.push.apply(targetOptions, optionsTail(vnode.state))
    }

    return modals.base(
      modals.header('Create Offer', vnode.attrs.cancelFn),
      modals.body(
        m('.container', [
          m('.text-muted.mb-2',
            'Enter info for your new Offer ',
            vnode.attrs.target
              ? `requesting ${vnode.attrs.target}`
              : `of ${vnode.attrs.source}`),
          layout.row([
            forms.textInput(setter('offer.label'), 'Label', false),
            forms.textInput(setter('offer.description'), 'Description', false)
          ]),
          m('hr'),
          mkt.bifold({
            header: layout.dropdown(
              getLabel(vnode.state.sourceLabel, 'Offered'),
              sourceOptions,
              'success'),
            body: forms.field(intSetter('offer.sourceQuantity'), {
              type: 'number'
            })
          }, {
            header: layout.dropdown(
              getLabel(vnode.state.targetLabel, 'Requested'),
              targetOptions,
              'success'),
            body: forms.field(intSetter('offer.targetQuantity'), {
              type: 'number',
              required: false,
              disabled: vnode.state.noTarget
            })
          }, 'right'),
          !vnode.state.hasNewAsset
            ? null
            : forms.group('New Asset', [
              resourceDropdown(
                vnode.state.asset.resource,
                resources,
                setter('asset.resource')),
              layout.row([
                assetField('Label', setter('asset.label')),
                assetField('Description', setter('asset.description'))
              ])
            ]),
          m('hr'),
          forms.group('Rules', [
            layout.row([
              ruleCheckbox(
                vnode.state,
                'EXCHANGE_ONCE',
                'Exchange only once'),
              ruleCheckbox(
                vnode.state,
                'EXCHANGE_ONCE_PER_ACCOUNT',
                'Exchange once per account')
            ]),
            layout.row(ruleCheckbox(
              vnode.state,
              'EXCHANGE_LIMITED_TO_ACCOUNTS',
              assetField(
                'Limit to public key',
                setter('asset.rules.EXCHANGE_LIMITED_TO_ACCOUNTS.keys'))))
          ])
        ])),
      modals.footer(
        modals.button('Cancel', vnode.attrs.cancelFn, 'secondary'),
        modals.button(
          'Create',
          submitter(vnode.state, vnode.attrs.acceptFn),
          'primary',
          { disabled: !isFormValid(vnode.state) })))
  }
}

/**
 * Displays a modal which will guide the user through creating an Offer
 */
const createOffer = (source = null, target = null) => {
  return modals.show(CreateOfferModal, { source, target })
    .catch(() => console.log('Creating offer canceled'))
}

module.exports = { createOffer }
