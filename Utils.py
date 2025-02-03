class ActionResult:
    def __init__(self, success: bool, message=None):
        self.success = success
        self.message = message