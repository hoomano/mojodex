import base64
import json
import os

from appstoreserverlibrary.api_client import AppStoreServerAPIClient
from flask import request
from flask_restful import Resource

from app import authenticate, db
from mojodex_core.entities.db_base_entities import *
from models.purchase_manager import PurchaseManager
from mojodex_backend_logger import MojodexBackendLogger
from appstoreserverlibrary.models.Environment import Environment

from mojodex_core.mail import send_admin_email
from mojodex_core.logging_handler import log_error
from datetime import datetime
class InAppApplePurchase(Resource):
    logger_prefix = "InAppApplePurchase Resource:: "

    def __init__(self):
        InAppApplePurchase.method_decorators = [authenticate(["PUT"])]
        self.logger = MojodexBackendLogger(f"{InAppApplePurchase.logger_prefix}")


    def _decode_apple_jws(self, jws_to_decode):
        try:
            # Parse signedPayload to identify the JWS header, payload, and signature representations.
            # Split the JWT token into header, payload, and signature
            header_base64url, payload_base64url, signature_base64url = jws_to_decode.split('.')
            # Decode the header from base64
            decoded_payload = base64.urlsafe_b64decode(payload_base64url + "===").decode("utf-8")
            # to json
            decoded_jws_payload = json.loads(decoded_payload)
            return decoded_jws_payload
        except Exception as e:
            raise Exception(f"decode_apple_jws : {e}")

    def __extract_info_from_decoded_transaction(self, decoded_transaction):
        try:
            # signed_transaction_info keys: ['transactionId', 'originalTransactionId', 'webOrderLineItemId', 'bundleId',
            # 'productId', 'subscriptionGroupIdentifier', 'purchaseDate', 'originalPurchaseDate', 'expiresDate',
            # 'quantity', 'type', 'inAppOwnershipType', 'signedDate', 'environment', 'transactionReason', 'storefront',
            # 'storefrontId', 'price', 'currency']
            transactionId = decoded_transaction[
                "transactionId"] if "transactionId" in decoded_transaction else None
            originalTransactionId = decoded_transaction[
                "originalTransactionId"] if "originalTransactionId" in decoded_transaction else None
            transactionReason = decoded_transaction[
                "transactionReason"] if "transactionReason" in decoded_transaction else None
            productId = decoded_transaction["productId"] if "productId" in decoded_transaction else None
            return transactionId, originalTransactionId, transactionReason, productId
        except Exception as e:
            raise Exception(f"__extract_info_from_decoded_transaction : {e}")


    # Apple callback
    def post(self):
        try:
            if not request.is_json:
                log_error(f"Error adding purchase : Request must be JSON", notify_admin=True)
                return {"error": "Request must be JSON"}, 400
        except Exception as e:
            log_error(f"Error on apple purchase webhook : Request must be JSON", notify_admin=True)
            return {"error": "Request must be JSON"}, 400

        try:
            signed_payload = request.json["signedPayload"]
        except Exception as e:
            log_error(f"Error on apple purchase webhook : Missing field signedPayload - request.json: {request.json}", notify_admin=True)
            return {"error": f"Missing field signedPayload"}, 400

        notificationType, notificationSubType = None, None
        transactionId, originalTransactionId = None, None
        purchase, user = None, None
        try:
            decoded_jws = self._decode_apple_jws(signed_payload)
            # decoded_jws keys: ['notificationType', 'subtype', 'notificationUUID', 'data', 'version', 'signedDate']
            notificationType = decoded_jws["notificationType"] # https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
            self.logger.debug(f"notificationType: {notificationType}")
            notificationSubType = decoded_jws["subtype"] if "subtype" in decoded_jws else None
            self.logger.debug(f"notificationSubType: {notificationSubType}")
            data = decoded_jws["data"]
            # data keys: ['appAppleId', 'bundleId', 'bundleVersion', 'environment', 'signedTransactionInfo', 'signedRenewalInfo', 'status']
            signed_transaction_info_jws = data["signedTransactionInfo"]
            signed_transaction_info = self._decode_apple_jws(signed_transaction_info_jws)
            transactionId, originalTransactionId, transactionReason, productId = self.__extract_info_from_decoded_transaction(signed_transaction_info)
            if transactionId is None:
                log_error(
                    f"Received apple purchase webhook with no transactionId")
                send_admin_email("🚨 URGENT: Apple purchase callback with no transactionId",
                                 PurchaseManager.purchases_email_receivers,
                                 f"signed_transaction_info : {signed_transaction_info}"
                                 f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - originalTransactionId: {originalTransactionId}")
                return {
                    "error": f"Apple purchase callback with no transactionId"}, 400


            self.logger.debug(f"transactionId: {transactionId}")
            self.logger.debug(f"originalTransactionId: {originalTransactionId}")
            self.logger.debug(f"transactionReason: {transactionReason}")
            self.logger.debug(f"productId: {productId}")

            purchase_manager = PurchaseManager()

            # Manage notificationType
            if (notificationType == "SUBSCRIBED" and notificationSubType in ["INITIAL_BUY", "RESUBSCRIBE"]) or notificationType == "DID_RENEW":
                    # Create purchase
                    # check purchase with this transactionId does not already exist => If yes, do nothing
                    purchase = db.session.query(MdPurchase).filter(MdPurchase.apple_transaction_id == transactionId).first()
                    if purchase is not None:
                        return {}, 200
                    self.logger.debug(f'Create purchase with transactionId: {transactionId} - originalTransactionId: {originalTransactionId}')
                    product = db.session.query(MdProduct).filter(MdProduct.product_apple_id == productId).first()
                    purchase = MdPurchase(
                        product_fk=product.product_pk,
                        creation_date=datetime.now(),
                        apple_transaction_id=transactionId,
                        apple_original_transaction_id=originalTransactionId,
                        active=False
                    )
                    db.session.add(purchase)
                    db.session.flush()
                    if notificationSubType == "BILLING_RECOVERY":
                        # The expired subscription that previously failed to renew has successfully renewed
                        # If last purchase is not active, activate it again
                        self.logger.debug('The expired subscription that previously failed to renew has successfully renewed')
                        send_admin_email( "Subscription renewed after billing recovery",
                                             PurchaseManager.purchases_email_receivers,
                            f"Subscription with originalTransactionId {originalTransactionId} and transactionId {transactionId} that previously failed to renew has successfully renewed."
                                      f"It has been re-activated")
                    elif notificationType == "DID_RENEW":
                        # just automatic renew
                        self.logger.debug('Automatic renew')
            else:
                # Be sure we have a purchase and a user associated to the originalTransactionId
                purchase = db.session.query(MdPurchase).filter(
                    MdPurchase.apple_transaction_id == originalTransactionId).first()
                if purchase is None:
                    log_error(
                        f"Purchase with transactionId {originalTransactionId} does not exist in mojodex db")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     PurchaseManager.purchases_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} subscription event but associated purchase was not found in db."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Purchase with apple_transaction_id {originalTransactionId} does not exist in mojodex db"}, 400

                if purchase.user_id is None:
                    log_error(f"Purchase with apple_transaction_id {originalTransactionId} has no user associated")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     PurchaseManager.purchases_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} - purchase_pk: {purchase.purchase_pk} - subscription event but associated purchase has no user associated."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Purchase with originalTransactionId {originalTransactionId} has no user associated"}, 400

                user = db.session.query(MdUser).filter(MdUser.user_id == purchase.user_id).first()
                if user is None:
                    log_error(f"Purchase with apple_transaction_id {originalTransactionId} has unknown user associated")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     PurchaseManager.purchases_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} - purchase_pk: {purchase.purchase_pk} - subscription event but associated purchase has unknown user associated."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Purchase with apple_transaction_id {originalTransactionId} has unknown user associated"}, 400


                    # else, it's just a renew, do nothing
                if notificationType == "DID_FAIL_TO_RENEW":
                    if notificationSubType == "GRACE_PERIOD":
                        # The subscription enters the billing retry period
                        # We should inform the user that there may be an issue with their billing information.
                        # But let access
                        self.logger.debug('The subscription enters the billing retry period')
                        # Send email to admins
                        send_admin_email("Subscription entering billing retry period",
                                            PurchaseManager.purchases_email_receivers,
                            f"Subscription of user {user.email} enters the billing retry period."
                                      f"We should inform them that there may be an issue with their billing information.\n"
                                      f"Access to purchase {purchase.purchase_pk} is still allowed.")
                    else:
                        # Stop access to service
                        self.logger.debug('Stop access to service')
                        purchase_manager.deactivate_purchase(purchase)
                        # Send email to admins
                        send_admin_email("Subscription ended",
                                         PurchaseManager.purchases_email_receivers,
                            f"Subscription of user {user.email} ended")


                elif notificationType == "EXPIRED":
                    # Stop access to service
                    self.logger.debug('Stop access to service')
                    # Send email to Admin with subtype to understand why
                    purchase_manager.deactivate_purchase(purchase)
                    # Send email to admins
                    send_admin_email(
                        "Subscription ended",
                        PurchaseManager.purchases_email_receivers,
                        f"Subscription of user {user.email} ended. notificationType=EXPIRED - Subtype: {notificationSubType}")
                else:
                    # Many possible causes, just send email to admin for manual check
                    self.logger.debug('Many possible causes, just send email to Admin for manual check')
                    send_admin_email(
                        "🚨 URGENT: Something unexpected happened on a purchase",
                        PurchaseManager.purchases_email_receivers,
                        f"notificationType={notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId} "
                        f"- OriginalTransactionID: {originalTransactionId} - purchase_pk: {purchase.purchase_pk} - user_email: {user.email}")

            db.session.commit()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error on apple purchase webhook : {e}")
            send_admin_email(
                "🚨 URGENT: Error happened on a purchase",
                PurchaseManager.purchases_email_receivers,
                f"notificationType={notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId} "
                f"- OriginalTransactionID: {originalTransactionId} - purchase_pk: {purchase.purchase_pk} - user_email: {user.email}")
            return {"error": f"Error on apple purchase webhook : {e}"}, 400


    def get_transaction_from_id(self, transaction_id):
        try:
            key_id = os.environ.get("APPLE_PRIVATE_KEY_ID")
            issuer_id = os.environ.get("APPLE_ISSUER_ID")
            bundle_id = os.environ.get("APPLE_BUNDLE_ID")
            environment = Environment.PRODUCTION if os.environ.get("APPLE_ENVIRONMENT")=="prod" else Environment.SANDBOX

            private_key = os.environ.get("APPLE_PRIVATE_KEY")
            private_key = private_key.replace(" ", "\n")
            private_key = "-----BEGIN PRIVATE KEY-----" + private_key + "-----END PRIVATE KEY-----"
            # to bytes
            private_key = private_key.encode()

            client = AppStoreServerAPIClient(private_key, key_id, issuer_id, bundle_id, environment)
            try:
                response = client.get_transaction_info(transaction_id)
            except Exception as e:
                raise Exception(f"get_transaction_from_id - client.get_transaction_info : {e}")
            transaction_info = response.signedTransactionInfo
            # decode
            decoded_jws_payload = self._decode_apple_jws(transaction_info)
            return decoded_jws_payload
        except Exception as e:
            raise Exception(f"get_transaction_from_id : {e}")


    # Associate user_id to purchase = verify transaction
    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error adding apple purchase : Request must be JSON", notify_admin=True)
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            transaction_id = request.json["transaction_id"]
        except KeyError as e:
            log_error(f"Error adding apple purchase : Missing field {e}", notify_admin=True)
            return {"error": f"Missing field {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if not user:
                log_error(f"Error adding purchase : Unknown user {user_id}")
                send_admin_email("🚨 URGENT: New client purchase error",
                                    PurchaseManager.purchases_email_receivers,
                                    f"Trying to associate user to a purchase but user {user_id} not found in mojodex db")
                return {"error": f"Unknown user {user_id}"}, 400


            result = db.session.query(MdPurchase, MdProduct)\
                .join(MdProduct, MdProduct.product_pk == MdPurchase.product_fk)\
                .filter(MdPurchase.apple_transaction_id == transaction_id).first()

            if not result:
                signed_transaction_info = self.get_transaction_from_id(transaction_id)
                transactionId, originalTransactionId, transactionReason, productId = self.__extract_info_from_decoded_transaction(
                    signed_transaction_info)
                if transactionId is None:
                    log_error(
                        f"Error adding purchase : transaction with no transactionId")
                    send_admin_email("🚨 URGENT: New client purchase error",
                                     PurchaseManager.purchases_email_receivers,
                                     f"PUT /purchase signed_transaction_info : {signed_transaction_info}")
                    return {
                        "error": f"Error adding purchase : transaction with no transactionId"}, 400
                # if it is
                # create purchase
                product = db.session.query(MdProduct).filter(MdProduct.product_apple_id == productId).first()
                purchase = MdPurchase(
                    product_fk=product.product_pk,
                    creation_date=datetime.now(),
                    apple_transaction_id=transactionId,
                    apple_original_transaction_id=originalTransactionId,
                    active=False
                )
                db.session.add(purchase)
                db.session.flush()
            else:
                purchase, product = result

            if purchase.user_id is not None:
                if purchase.user_id != user_id:
                    log_error(f"Error adding purchase : Purchase with apple_transaction_id {transaction_id} already has a different user associated")
                    send_admin_email("🚨 URGENT: New client purchase error",
                                        PurchaseManager.purchases_email_receivers,
                                        f"Trying to associate user to a purchase but purchase with apple_transaction_id {transaction_id} already has a different user associated")
                    return {"error": f"Purchase with apple_transaction_id {transaction_id} already has a different user associated"}, 400
                else:
                    self.logger.debug(f"Purchase with apple_transaction_id {transaction_id} already has a user but same one")
                    return {}, 200

            purchase_manager = PurchaseManager()
            if not product.n_days_validity: # product is a subscription
                if purchase_manager.user_has_active_subscription(user_id):
                    return {"error": f"User already has an active subscription"}, 400

            purchase.user_id = user_id

            purchase.completed_date = datetime.now()
            if purchase.apple_original_transaction_id == purchase.apple_transaction_id: # NEW PURCHASE
                send_admin_email(subject="🥳 New client purchase",
                                 recipients=PurchaseManager.purchases_email_receivers,
                                 text=f"🎉 Congratulations ! {user.email} just bought {product.label} !")
            # Activate purchase
            purchase_manager.activate_purchase(purchase)

            db.session.commit()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error adding apple purchase - transactionId: {transaction_id}: {e}", notify_admin=True)
            return {"error": f"Error adding purchase: {e}"}, 400







