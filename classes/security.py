import random

class Security:
    def __init__(self, issuer=None, security_id=None) -> None:
        self.issuer = issuer
        self.security_id = security_id

    def __hash__(self):
        if self.security_id is not None: return self.security_id.__hash__()
        if not hasattr(self, "__random_hash__"): self.__random_hash__ = random.getrandbits(64)
        return self.__random_hash__