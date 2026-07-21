from protocol.message_types import MessageType


def make_message(
    message_type: MessageType,
    seq_num: int,
    **kwargs
) -> dict:

    message = {
        "type": message_type.value,
        "seq_num": seq_num
    }

    message.update(kwargs)

    return message