import imapclient

def encode_to_imap_utf7(text):
    """将文本编码为IMAP UTF-7格式"""
    return imapclient.imap_utf7.encode(text).decode('ascii')


def decode_from_imap_utf7(encoded_text):
    """将IMAP UTF-7格式解码为文本"""
    return imapclient.imap_utf7.decode(encoded_text.encode('ascii'))