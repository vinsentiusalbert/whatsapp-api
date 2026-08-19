from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    receiver: str
    message: str
