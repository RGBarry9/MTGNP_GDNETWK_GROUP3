def validate(message: dict):

    if "type" not in message:
        raise ValueError("Missing 'type' field.")

    if "seq_num" not in message:
        raise ValueError("Missing 'seq_num' field.")