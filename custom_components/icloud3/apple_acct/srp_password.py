"""SRP password handling."""

from ..utils.messaging   import (_log, )

from hashlib import pbkdf2_hmac, sha256

class SrpProtocolType():
    """SRP password types."""

    S2K = "s2k"
    S2K_FO = "s2k_fo"


class SrpPassword:
    """
    Encode SRP password

    This provides an encoded password based on the actual password and the salt value using the
    iterations and key_length parameters.

    1. Create and initialize this class object before calling the srp.User. Then, this object is
    passed instead of the actual password. srp.User will call the SrpEncodePW.encode() function to
    encode the password for the final m1 & m2 public key calculations.

        SrpPW   = SrpEncodePassword(password)
        SrpUser = srp.User(username, SrpEncodePW, hash_alg=srp.SHA256, ng_type=srp.NG_2048)

    2. Once the salt, iterations & key_length are known, pass them to this class object to be set
    for later use..

        SrpPW.set_encrypt_info(salt, iterations, key_length)

    3. srp.User will call the password.encode() function below to encode the password for the m1
    public key calculations

        m1_srpusr = SrpUser.process_challenge(salt, b)

    """

    def __init__(self, password: str) -> None:
        self.password = password
        self._password_hash: bytes = sha256(password.encode("utf-8")).digest()
        self.salt: bytes | None = None
        self.iterations: int | None = None
        self.key_length: int | None = None
        self.protocol: SrpProtocolType | None = None
        self.error_reason: str | None = None

    def set_encrypt_info(
        self, salt: bytes, iterations: int, key_length: int, protocol: SrpProtocolType
    ) -> None:
        """Set encrypt info."""
        self.salt = salt
        self.iterations = iterations
        self.key_length = key_length
        self.protocol = protocol

    def encode(self) -> bytes:
        """Encode password."""
        if self.salt is None or self.iterations is None or self.key_length is None:
            self.error_reason = f"Failed to setup salt/hash values"
            raise ValueError(self.error_reason)

        password_digest: bytes | None = None

        if self.protocol == SrpProtocolType.S2K_FO:
            password_digest = self._password_hash.hex().encode()
        elif self.protocol == SrpProtocolType.S2K:
            password_digest = self._password_hash

        if password_digest is None:
            self.error_reason= (f"Acct/Password uses unsupported Protocol Type ({self.protocol}), "
                                f"Password may need to be changed")
            raise ValueError(self.error_reason)

        return pbkdf2_hmac(
            "sha256",
            password_digest,
            self.salt,
            self.iterations,
            self.key_length,
        )
