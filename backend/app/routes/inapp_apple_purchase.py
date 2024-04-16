import base64
import json
import os

from appstoreserverlibrary.api_client import AppStoreServerAPIClient
from flask import request
from flask_restful import Resource
from datetime import datetime
from app import authenticate, db
from mojodex_core.entities import *
from models.role_manager import RoleManager
from mojodex_backend_logger import MojodexBackendLogger
from appstoreserverlibrary.models.Environment import Environment

from mojodex_core.mail import send_admin_email
from mojodex_core.logging_handler import log_error

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
                log_error(f"Error adding role : Request must be JSON", notify_admin=True)
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
        role, user = None, None
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
                                 RoleManager.roles_email_receivers,
                                 f"signed_transaction_info : {signed_transaction_info}"
                                 f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - originalTransactionId: {originalTransactionId}")
                return {
                    "error": f"Apple purchase callback with no transactionId"}, 400


            self.logger.debug(f"transactionId: {transactionId}")
            self.logger.debug(f"originalTransactionId: {originalTransactionId}")
            self.logger.debug(f"transactionReason: {transactionReason}")
            self.logger.debug(f"productId: {productId}")

            role_manager = RoleManager()

            # Manage notificationType
            if (notificationType == "SUBSCRIBED" and notificationSubType in ["INITIAL_BUY", "RESUBSCRIBE"]) or notificationType == "DID_RENEW":
                    # Create role
                    # check role with this transactionId does not already exist => If yes, do nothing
                    role = db.session.query(MdRole).filter(MdRole.apple_transaction_id == transactionId).first()
                    if role is not None:
                        return {}, 200
                    self.logger.debug(f'Create role with transactionId: {transactionId} - originalTransactionId: {originalTransactionId}')
                    profile = db.session.query(MdProfile).filter(MdProfile.product_apple_id == productId).first()
                    role = MdRole(
                        profile_fk=profile.profile_pk,
                        creation_date=datetime.now(),
                        apple_transaction_id=transactionId,
                        apple_original_transaction_id=originalTransactionId,
                        active=False
                    )
                    db.session.add(role)
                    db.session.flush()
                    if notificationSubType == "BILLING_RECOVERY":
                        # The expired subscription that previously failed to renew has successfully renewed
                        # If last role is not active, activate it again
                        self.logger.debug('The expired subscription that previously failed to renew has successfully renewed')
                        send_admin_email( "Subscription renewed after billing recovery",
                                             RoleManager.roles_email_receivers,
                            f"Subscription with originalTransactionId {originalTransactionId} and transactionId {transactionId} that previously failed to renew has successfully renewed."
                                      f"It has been re-activated")
                    elif notificationType == "DID_RENEW":
                        # just automatic renew
                        self.logger.debug('Automatic renew')
            else:
                # Be sure we have a role and a user associated to the originalTransactionId
                role = db.session.query(MdRole).filter(
                    MdRole.apple_transaction_id == originalTransactionId).first()
                if role is None:
                    log_error(
                        f"Role with transactionId {originalTransactionId} does not exist in mojodex db")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     RoleManager.roles_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} subscription event but associated role was not found in db."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Role with apple_transaction_id {originalTransactionId} does not exist in mojodex db"}, 400

                if role.user_id is None:
                    log_error(f"Role with apple_transaction_id {originalTransactionId} has no user associated")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     RoleManager.roles_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} - role_pk: {role.role_pk} - subscription event but associated role has no user associated."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Role with originalTransactionId {originalTransactionId} has no user associated"}, 400

                user = db.session.query(MdUser).filter(MdUser.user_id == role.user_id).first()
                if user is None:
                    log_error(f"Role with apple_transaction_id {originalTransactionId} has unknown user associated")
                    send_admin_email("🚨 URGENT: Subscription error",
                                     RoleManager.roles_email_receivers,
                                        f"Apple originalTransactionId {originalTransactionId} - role_pk: {role.role_pk} - subscription event but associated role has unknown user associated."
                                        f"\nEvent: NOTIFICATION_TYPE: {notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId}")
                    return {
                        "error": f"Role with apple_transaction_id {originalTransactionId} has unknown user associated"}, 400


                    # else, it's just a renew, do nothing
                if notificationType == "DID_FAIL_TO_RENEW":
                    if notificationSubType == "GRACE_PERIOD":
                        # The subscription enters the billing retry period
                        # We should inform the user that there may be an issue with their billing information.
                        # But let access
                        self.logger.debug('The subscription enters the billing retry period')
                        # Send email to admins
                        send_admin_email("Subscription entering billing retry period",
                                            RoleManager.roles_email_receivers,
                            f"Subscription of user {user.email} enters the billing retry period."
                                      f"We should inform them that there may be an issue with their billing information.\n"
                                      f"Access to role {role.role_pk} is still allowed.")
                    else:
                        # Stop access to service
                        self.logger.debug('Stop access to service')
                        role_manager.deactivate_role(role)
                        # Send email to admins
                        send_admin_email("Subscription ended",
                                         RoleManager.roles_email_receivers,
                            f"Subscription of user {user.email} ended")


                elif notificationType == "EXPIRED":
                    # Stop access to service
                    self.logger.debug('Stop access to service')
                    # Send email to Admin with subtype to understand why
                    role_manager.deactivate_role(role)
                    # Send email to admins
                    send_admin_email(
                        "Subscription ended",
                        RoleManager.roles_email_receivers,
                        f"Subscription of user {user.email} ended. notificationType=EXPIRED - Subtype: {notificationSubType}")
                else:
                    # Many possible causes, just send email to admin for manual check
                    self.logger.debug('Many possible causes, just send email to Admin for manual check')
                    send_admin_email(
                        "🚨 URGENT: Something unexpected happened on a role",
                        RoleManager.roles_email_receivers,
                        f"notificationType={notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId} "
                        f"- OriginalTransactionID: {originalTransactionId} - role_pk: {role.role_pk} - user_email: {user.email}")

            db.session.commit()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error on apple purchase webhook : {e}")
            send_admin_email(
                "🚨 URGENT: Error happened on a role",
                RoleManager.roles_email_receivers,
                f"notificationType={notificationType} - Subtype: {notificationSubType} - TransactionID: {transactionId} "
                f"- OriginalTransactionID: {originalTransactionId} - role_pk: {role.role_pk} - user_email: {user.email}")
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


    # Associate user_id to role = verify transaction
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
                send_admin_email("🚨 URGENT: New client role error",
                                    RoleManager.roles_email_receivers,
                                    f"Trying to associate user to a role but user {user_id} not found in mojodex db")
                return {"error": f"Unknown user {user_id}"}, 400


            result = db.session.query(MdRole, MdProfile)\
                .join(MdProfile, MdProfile.profile_pk == MdRole.profile_fk)\
                .filter(MdRole.apple_transaction_id == transaction_id).first()

            if not result:
                signed_transaction_info = self.get_transaction_from_id(transaction_id)
                transactionId, originalTransactionId, transactionReason, productId = self.__extract_info_from_decoded_transaction(
                    signed_transaction_info)
                if transactionId is None:
                    log_error(
                        f"Error adding role : transaction with no transactionId")
                    send_admin_email("🚨 URGENT: New client role error",
                                     RoleManager.roles_email_receivers,
                                     f"PUT /purchase signed_transaction_info : {signed_transaction_info}")
                    return {
                        "error": f"Error adding role : transaction with no transactionId"}, 400
                # if it is
                # create role
                profile = db.session.query(MdProfile).filter(MdProfile.product_apple_id == productId).first()
                role = MdRole(
                    profile_fk=profile.profile_pk,
                    creation_date=datetime.now(),
                    apple_transaction_id=transactionId,
                    apple_original_transaction_id=originalTransactionId,
                    active=False
                )
                db.session.add(role)
                db.session.flush()
            else:
                role, profile = result

            if role.user_id is not None:
                if role.user_id != user_id:
                    log_error(f"Error adding role : Role with apple_transaction_id {transaction_id} already has a different user associated")
                    send_admin_email("🚨 URGENT: New client role error",
                                        RoleManager.roles_email_receivers,
                                        f"Trying to associate user to a role but role with apple_transaction_id {transaction_id} already has a different user associated")
                    return {"error": f"Role with apple_transaction_id {transaction_id} already has a different user associated"}, 400
                else:
                    self.logger.debug(f"Role with apple_transaction_id {transaction_id} already has a user but same one")
                    return {}, 200

            role_manager = RoleManager()
            if not profile.n_days_validity: # profile is a subscription
                if role_manager.user_has_active_subscription(user_id):
                    return {"error": f"User already has an active subscription"}, 400

            role.user_id = user_id

            role.completed_date = datetime.now()
            if role.apple_original_transaction_id == role.apple_transaction_id: # NEW ROLE
                send_admin_email(subject="🥳 New client role",
                                 recipients=RoleManager.roles_email_receivers,
                                 text=f"🎉 Congratulations ! {user.email} just bought {profile.label} !")
            # Activate role
            role_manager.activate_role(role)

            db.session.commit()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error adding apple role - transactionId: {transaction_id}: {e}", notify_admin=True)
            return {"error": f"Error adding role: {e}"}, 400







