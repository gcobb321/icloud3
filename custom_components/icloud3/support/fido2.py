from fido2.client import Fido2Client
from fido2.ctap2 import AttestationObject, AuthenticatorData
from fido2.server import Fido2Server
from fido2.utils import websafe_encode, websafe_decode
import json

'''
ChatGPT question:
Create a Python program to authenticate access to an Apple account using Fido based hardware security keys


Key Points:
	1.	Registration: The program generates a registration challenge, which the user completes with their hardware security key.
	2.	Authentication: Once registered, the program can authenticate the user by verifying the hardware key’s response to an authentication challenge.
	3.	Customization: Replace https://localhost with your actual client application origin, and ensure the RP ID matches the relying party’s domain (e.g., apple.com).

Notes:
	•	This example assumes a local FIDO2 client and server setup. Real-world integration with Apple’s services may require working within their APIs or using a browser-based flow.
	•	You may need additional permissions or SDKs from Apple to fully integrate with Apple account authentication.
'''



# FIDO2 Relying Party information
RP_ID = "apple.com"  # Use Apple's domain for RP ID
RP_NAME = "Apple"
ORIGIN = "https://apple.com"

# Create a FIDO2 server instance
server = Fido2Server({"id": RP_ID, "name": RP_NAME})


def register_security_key():
    # Generate a registration challenge
    registration_data, state = server.register_begin(
        {
            "id": b"user-id",
            "name": "User Name",
            "displayName": "User Display Name",
        },
        user_verification="discouraged",
    )

    print("Registration Challenge:", json.dumps(registration_data, indent=2))

    # Assume user interacts with a security key via a client
    client = Fido2Client("https://localhost", origin=ORIGIN)
    client_data, attestation_object = client.make_credential(
        registration_data["publicKey"]
    )

    # Verify the registration response
    auth_data = server.register_complete(
        state,
        client_data,
        AttestationObject(attestation_object),
    )

    print("Registration successful!")
    print("Authenticator Data:", websafe_encode(auth_data))


def authenticate_with_security_key():
    # Generate an authentication challenge
    auth_data, state = server.authenticate_begin([{
        "id": b"user-id",
        "name": "User Name",
        "displayName": "User Display Name",
    }])

    print("Authentication Challenge:", json.dumps(auth_data, indent=2))

    # Assume user interacts with a security key via a client
    client = Fido2Client("https://localhost", origin=ORIGIN)
    client_data, auth_data = client.get_assertion(auth_data["publicKey"])

    # Verify the authentication response
    server.authenticate_complete(
        state,
        [AuthenticatorData(websafe_decode(auth_data))],
        client_data,
        [websafe_decode(auth_data)],
    )

    print("Authentication successful!")


if __name__ == "__main__":
    print("FIDO2 Security Key Authentication for Apple Account")
    choice = input("Enter '1' to register or '2' to authenticate: ").strip()

    if choice == "1":
        register_security_key()
    elif choice == "2":
        authenticate_with_security_key()
    else:
        print("Invalid choice. Exiting.")