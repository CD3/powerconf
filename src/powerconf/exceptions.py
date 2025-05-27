class UndefinedVariableInExpression(RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)


class SyntaxErrorInExpression(RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)


class InvalidConfiguration(RuntimeError):
    def __init__(self, msg):
        super().__init__(msg)
