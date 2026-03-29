import razorpay

try:
    client = razorpay.Client(auth=("rzp_test_SX67UWoUz2nyYC", "szfmC6M3VVR7aBxyVIWK4xKN"))
    order_data = {
        "amount": 100,
        "currency": "INR",
        "receipt": "test_receipt",
        "payment_capture": "1"
    }
    order = client.order.create(data=order_data)
    print("SUCCESS", order)
except Exception as e:
    print("ERROR:", e)
