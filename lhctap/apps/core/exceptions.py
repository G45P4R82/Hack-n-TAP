class LHCTapException(Exception):
    """Exceção base para o sistema LHC Tap"""
    pass


class InsufficientBalanceError(LHCTapException):
    """Saldo insuficiente para operação"""
    pass


class TokenExpiredError(LHCTapException):
    """Token expirado ou inválido"""
    pass


class TokenAlreadyUsedError(LHCTapException):
    """Token já foi utilizado"""
    pass


class RateLimitExceededError(LHCTapException):
    """Rate limit excedido"""
    pass


class TapInactiveError(LHCTapException):
    """Tap está inativo"""
    pass
