
from sawtooth_sdk.processor.exceptions import InvalidTransaction

from marketplace_processor.protobuf import transfer_pb2


def handle_transfer_asset(transfer_asset, header, state):

    """Handle Offer acceptance.

    Args:
        accept_offer (AcceptOffer): The transaction.
        header (TransactionHeader): The TransactionHeader.
        state (MarketplaceState): The wrapper around the context.

    Raises:
        - InvalidTransaction
            - The Offer does not exist or is not Open
            - The receiver source Asset does not exist.
            - The receiver target Asset does not exist.
            - The offerer source asset resource does not match the
              receiver target asset resource.
            - The offerer target asset resource does not match the
              the receiver source asset resource.
            - The receiver source asset does not have the required quantity.
            - The offerer source asset does not have the required quantity.
    """
    print("transfer_asset =======> ",transfer_asset)
    transfer = state.get_transfer(identifier=transfer_asset.id,
                                    account = header.signer_public_key)


    check_validity_of_transfer(transfer)

    transfer_asset = TeansferAsset(transfer, header, state)

    # The asset ids referernce Assets.
    transfer_asset.validate_output_asset_exists()

    transfer_asset.validate_input_asset_exists()

    # The resources match for the Assets
    transfer_asset.validate_input_asset_resources()

    transfer_asset.validate_output_asset_resources()


    # There is enough in each Asset to make the transaction.
    transfer_asset.validate_output_enough(transfer.amount)


    # Handle incrementing and decrementing the Assets' quantity
    transfer_asset.handle_sender_source(transfer.amount)
    transfer_asset.handle_receiver_target(transfer.amount)



def check_validity_of_transfer(transfer):

    if not transfer:
        raise InvalidTransaction(
            "Failed to accept Offer, Offer {} does not exist".format(
                transfer.id))


class TeansferAsset(object):

    def __init__(self, transfer, header, state):
        self._transfer = transfer
        self._header = header

        self._state = state


        source_hldng = state.get_asset(transfer.source)
        target_hldng = state.get_asset(transfer.target)

        resource = state.get_resource(target_hldng.resource)

        self._sender_asset = source_hldng
        self._receiver_asset = target_hldng


    def validate_output_asset_exists(self):
        if self._transfer.target and self._transfer.source:
            if self._sender_asset and not self._receiver_asset:
                raise InvalidTransaction(
                    "self._sender_asset and not self._receiver_asset ")

    def validate_input_asset_exists(self):
        if not self._receiver_asset:
            raise InvalidTransaction(
                "Failed to not self._receiver_asset ")

    def validate_input_asset_resources(self):
        if not self._sender_asset.resource == self._receiver_asset.resource:
            raise InvalidTransaction(
                "self._sender_asset.resource == self._receiver_asset.resource ")

    def validate_output_asset_resources(self):
        if self._transfer.target \
                and self._sender_asset \
                and not \
                self._sender_asset.resource == self._receiver_asset.resource:
            raise InvalidTransaction(
                "Failed to accept offer, expected Asset resource {}, got "
                "resource {}.".format(self._sender_asset.resource,
                                   self._receiver_asset.resource))

    def validate_output_enough(self, output_quantity):
        if self._accept_offer.source and \
                output_quantity > self._sender_asset.quantity:
            raise InvalidTransaction(
                "Failed to accept offer, needed quantity {}, but only had {} "
                "of {}".format(output_quantity,
                               self._sender_asset.quantity,
                               self._sender_asset.resource))

    def handle_sender_source(self, input_quantity):
        
        self._state.change_asset_quantity(
            self._sender_asset.id,
            self._sender_asset.quantity - input_quantity)

    def handle_receiver_target(self, input_quantity):
        self._state.change_asset_quantity(
            self._receiver_asset.id,
            self._receiver_asset.quantity + input_quantity)

