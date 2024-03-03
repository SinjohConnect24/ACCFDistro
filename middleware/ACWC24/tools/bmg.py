import json

from middleware.ACWC24.tools.bitconv import *


def _decode_esc_sequence(esc) -> str:
    esc_len = esc[0x2] & 0xFF
    esc_type = esc[0x3] & 0xFF

    ret_str = "{"
    for b in esc:
        ret_str += "{0:02X}".format(b)
    ret_str += "}"
    return ret_str


def _decode_string(data, off: int = 0) -> str:
    ret_str = ""

    while True:
        char = data[off:off + 2].decode('utf-16be')

        if ord(char) == 0x0000:
            return ret_str
        elif ord(char) == 0x001A:
            esc_len = get_uint8(data, off + 0x2)
            ret_str += _decode_esc_sequence(data[off:off + esc_len])
            off += esc_len
        else:
            ret_str += char
            off += 2


def _encode_esc_sequence(esc_string: str) -> bytearray:
    esc_string = esc_string[1:len(esc_string) - 1]
    esc_params = esc_string.split('=')

    return bytearray.fromhex(esc_string)


def _encode_string(message: str):
    null_terminator = '\0'.encode("utf-16be")

    if not message or message == "":
        return null_terminator

    encoded = bytearray()
    cur_idx = 0

    while cur_idx < len(message):
        cur_char = message[cur_idx]

        if cur_char == '{':
            closing_idx = cur_idx + 1

            while closing_idx < len(message):
                if message[closing_idx] == '}':
                    encoded += _encode_esc_sequence(message[cur_idx:closing_idx + 1])
                    cur_idx = closing_idx + 1
                    break
                else:
                    closing_idx += 1
        else:
            encoded += cur_char.encode("utf-16be")
            cur_idx += 1

    encoded += null_terminator

    return encoded


NUM_SECTIONS = 3
MESSAGE_SIZE = 20
MESGID_SIZE = 4
MESG_MAGIC = 0x4D455347
bmg1_MAGIC = 0x626D6731
INF1_MAGIC = 0x494E4631
DAT1_MAGIC = 0x44415431
MID1_MAGIC = 0x4D494431


class Message:
    def __init__(self):
        self.text = None
        self.offText = 0
        self.unk4 = None

    @staticmethod
    def unpack(buf, off):
        m = Message()
        m.offText = get_uint32(buf, off + 0x00)
        m.unk4 = get_bytes(buf, off + 0x04, 0x10)
        return m

    def pack(self) -> bytes:
        b = bytearray(MESSAGE_SIZE)
        put_uint32(b, 0x00, self.offText)
        put_bytes(b, 0x04, self.unk4)
        return bytes(b)


class Bmg:
    def __init__(self):
        self._messages = []

    def get_messages(self):
        return self._messages

    def load(self, buf):
        self.get_messages().clear()

        if not buf:
            return

        if not (get_uint32(buf, 0x00) == MESG_MAGIC and get_uint32(buf, 0x04) == bmg1_MAGIC):
            raise Exception("Error: Buffer does not contain MESGbmg1 data.")

        file_size = get_uint32(buf, 0x08)
        sections = get_uint32(buf, 0x0C)
        encoding = get_uint8(buf, 0x10)

        # INF1
        cur = 0x20
        section_size = get_uint32(buf, cur + 0x04)
        num_messages = get_uint16(buf, cur + 0x08)
        len_messages = get_uint16(buf, cur + 0x0A)

        for i in range(num_messages):
            message = Message.unpack(buf, cur + 0x10 + len_messages * i)
            message.text = _decode_string(buf, cur + section_size + 0x8 + message.offText)
            self.get_messages().append(message)

        # DAT1
        cur += section_size
        section_size = get_uint32(buf, cur + 0x04)
        # already parsed through previous section

        # MID1
        cur += section_size
        section_size = get_uint32(buf, cur + 0x04)
        # this is just a list of the message indices in ascending order

        return self

    def save(self) -> bytes:
        num_messages = len(self.get_messages())
        len_inf1 = align32(0x10 + MESSAGE_SIZE * num_messages)
        out_data = bytearray(0x20 + len_inf1 + 0x8)

        out_strings = bytearray()
        strings = {}

        put_uint32(out_data, 0x00, MESG_MAGIC)
        put_uint32(out_data, 0x04, bmg1_MAGIC)
        put_uint32(out_data, 0x0C, NUM_SECTIONS)
        put_uint8(out_data, 0x10, 2)  # encoding should always be utf-16be

        # INF1
        cur = 0x20
        put_uint32(out_data, cur, INF1_MAGIC)
        put_uint32(out_data, cur + 0x4, len_inf1)
        put_uint16(out_data, cur + 0x8, num_messages)
        put_uint16(out_data, cur + 0xA, MESSAGE_SIZE)

        for i in range(num_messages):
            cur_entry = cur + 0x10 + MESSAGE_SIZE * i
            message = self.get_messages()[i]

            if message.text in strings:
                message.offText = strings[message.text]
            else:
                message.offText = len(out_strings)
                strings[message.text] = message.offText
                out_strings += _encode_string(message.text)

            put_bytes(out_data, cur_entry, message.pack())

        # DAT1
        cur += len_inf1
        len_dat1 = align32(0x8 + len(out_strings))

        put_uint32(out_data, cur, DAT1_MAGIC)
        put_uint32(out_data, cur + 0x4, len_dat1)
        out_data += out_strings
        out_data += bytearray(align32(len(out_data)) - len(out_data))

        # MID1
        cur += len_dat1
        len_mid1 = align32(0x10 + num_messages * MESGID_SIZE)
        out_data += bytearray(len_mid1)

        put_uint32(out_data, cur, MID1_MAGIC)
        put_uint32(out_data, cur + 0x4, len_mid1)
        put_uint16(out_data, cur + 0x8, num_messages)
        put_uint8(out_data, cur + 0xA, 16)

        for i in range(num_messages):
            put_uint32(out_data, cur + 0x10 + i * MESGID_SIZE, i)

        put_uint32(out_data, 0x08, len(out_data))

        return bytes(out_data)


def from_json(path: str):
    bmg = Bmg()

    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)

    for mentry in data["Messages"]:
        message = Message()

        message.text = mentry["Text"]
        message.unk4 = bytes.fromhex(mentry["Attr"])

        bmg.get_messages().append(message)

    return bmg


def to_json(bmg, path: str):
    dump = dict()
    msgd = list()
    dump["Messages"] = msgd

    for message in bmg.get_messages():
        mentry = dict()
        mentry["Attr"] = "".join(["{0:02X}".format(b) for b in message.unk4])
        mentry["Text"] = message.text
        msgd.append(mentry)

    with open(path, "w", encoding="utf8") as f:
        json.dump(dump, f, ensure_ascii=False, indent=4)
        f.flush()
