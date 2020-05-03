def get_symbol_from_exc_msg(msg):
    try:
        return msg['data'][0]['symbol']
    except KeyError:
        return None

