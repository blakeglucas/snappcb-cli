class IsolationRoutingException(Exception):
    def __init__(self, message: str):
        super().__init__(f'[Iso Error]: {message}')


class NccRoutingException(Exception):
    def __init__(self, message: str):
        super().__init__(f'[NCC Error]: {message}')


class DrillingException(Exception):
    def __init__(self, message: str):
        super().__init__(f'[Drill Error]: {message}')


class DrillSizeException(DrillingException):
    def __init__(self, drill_dia_mm: float):
        super().__init__(f"Drill size of {drill_dia_mm}mm is too large for all holes")