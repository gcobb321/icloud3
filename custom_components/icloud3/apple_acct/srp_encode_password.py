"""SRP password handling."""

import hashlib
from ..utils.messaging   import (_log, )


class SrpEncodePassword:
    """
    Encode SRP password

    This provides an encoded password based on the actual password and the salt value using the
    iterations and key_length parameters.

    1. Create and initialize this class object before calling the srp.User. Then, this object is
    passed instead of the actual password. srp.User will call the SrpEncodePW.encode() function to
    encode the password for the final m1 & m2 public key calculations.

        SrpEncodePW = SrpEncodePassword(password)
        SrpUser     = srp.User(username, SrpEncodePW, hash_alg=srp.SHA256, ng_type=srp.NG_2048)

    2. Once the salt, iterations & key_length are known, pass them to this class object to be set
    for later use..

        SrpEncodePW.set_encrypt_info(salt, iterations, key_length)

    3. srp.User will call the password.encode() function below to encode the password for the m1
    public key calculations

        m1_srpusr = SrpUser.process_challenge(salt, b)

    """

    def __init__(self, password: str) -> None:
        self._password_hash: bytes = hashlib.sha256(password.encode("utf-8")).digest()
        self.salt: bytes | None = None
        self.iterations: int | None = None
        self.key_length: int | None = None

    def set_encrypt_info(self, salt: bytes, iterations: int, key_length: int) -> None:
        """Set encrypt info."""
        self.salt = salt
        self.iterations = iterations
        self.key_length = key_length

    def encode(
        self,
    ) -> bytes:
        """Encode password."""
        if self.salt is None or self.iterations is None or self.key_length is None:
            raise ValueError("Encrypt info not set")

        return hashlib.pbkdf2_hmac(
            "sha256",
            self._password_hash,
            self.salt,
            self.iterations,
            self.key_length,
        )
