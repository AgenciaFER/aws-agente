class ClientError(Exception):
    def __init__(self, error_response=None, operation_name=None):
        super().__init__(str(error_response))
        self.response = error_response or {'Error': {'Code': 'Error', 'Message': 'Client error'}}
        self.operation_name = operation_name
class NoCredentialsError(Exception):
    pass
