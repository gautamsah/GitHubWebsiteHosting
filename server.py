import logging
import os
from flask import Flask, request
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.api_helper import ApiHelper

# Flask application setup
app = Flask(__name__)

# Environment variables for PayPal credentials
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
    raise EnvironmentError(
        "PayPal Client ID and Secret must be set as environment variables."
    )

# PayPal client configuration
paypal_client: PaypalServersdkClient = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=PAYPAL_CLIENT_ID,
        o_auth_client_secret=PAYPAL_CLIENT_SECRET,
    ),
    logging_configuration=LoggingConfiguration(
        log_level=logging.INFO,
        mask_sensitive_headers=False,  # Disable masking for sandbox testing
        request_logging_config=RequestLoggingConfiguration(log_headers=True, log_body=True),
        response_logging_config=ResponseLoggingConfiguration(log_headers=True, log_body=True),
    ),
)

@app.route("/", methods=["GET"])
def index():
    return {"message": "Server is running"}

orders_controller: OrdersController = paypal_client.orders

@app.route("/api/orders", methods=["POST"])
def create_order():
    request_body = request.get_json()
    cart = request_body.get("cart", [])
    order = orders_controller.orders_create(
        {
            "body": OrderRequest(
                intent=CheckoutPaymentIntent.CAPTURE,
                purchase_units=[
                    PurchaseUnitRequest(
                        AmountWithBreakdown(currency_code="USD", value="100.00")
                    )
                ],
            ),
            "prefer": "return=representation",
        }
    )
    return ApiHelper.json_serialize(order.body)

@app.route("/api/orders/<order_id>/capture", methods=["POST"])
def capture_order(order_id):
    order = orders_controller.orders_capture(
        {"id": order_id, "prefer": "return=representation"}
    )
    return ApiHelper.json_serialize(order.body)

if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", 8080)), host="0.0.0.0")
