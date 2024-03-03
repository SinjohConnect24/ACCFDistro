from middleware.ACWC24.tools.bitconv import *

U8_MAGIC = 0x55AA382D
NODE_SIZE = 0xC
ROOT_OFFSET = 0x20


class _U8Node:
    def __init__(self):
        self.isDir = False
        self.offName = 0
        self.off_data = 0
        self.lenData = 0

    @staticmethod
    def unpack(buf, off):
        e = _U8Node()
        e.isDir = get_bool(buf, off + 0x00)
        e.offName = get_uint24(buf, off + 0x01)
        e.off_data = get_uint32(buf, off + 0x04)
        e.lenData = get_uint32(buf, off + 0x08)
        return e

    def pack(self) -> bytes:
        b = bytearray(NODE_SIZE)
        put_bool(b, 0x00, self.isDir)
        put_uint24(b, 0x01, self.offName)
        put_uint32(b, 0x04, self.off_data)
        put_uint32(b, 0x08, self.lenData)
        return bytes(b)


class U8:
    def __init__(self):
        self._files = {}

    def load(self, buf):
        if not buf:
            return

        if get_uint32(buf, 0x00) != U8_MAGIC:
            raise Exception("Error: Buffer does not contain U8 data.")

        off_root = get_uint32(buf, 0x04)
        len_nodes = get_uint32(buf, 0x08)
        off_data = get_uint32(buf, 0x0C)

        root_node = _U8Node.unpack(buf, off_root)
        nodes = [
            _U8Node.unpack(buf, off_root + NODE_SIZE * (i + 1))
            for i in range(root_node.lenData - 1)
        ]
        strings_pos = off_root + root_node.lenData * NODE_SIZE

        recursion = [root_node.lenData]
        recursion_dir = []
        counter = 0
        for node in nodes:
            counter += 1
            name = get_string(buf, strings_pos + node.offName, "latin-1")

            if node.isDir:
                path = "/".join(recursion_dir + [name])
                recursion.append(node.lenData)
                recursion_dir.append(name)
                self._files[path] = None
            else:
                path = "/".join(recursion_dir + [name])
                data = buf[node.off_data : node.off_data + node.lenData]
                self._files[path] = data

            if len(recursion_dir):
                sz = recursion.pop()
                if sz != counter + 1:
                    recursion.append(sz)
                else:
                    recursion_dir.pop()

    def save(self):
        buf = bytearray(0x20)
        put_uint32(buf, 0x00, U8_MAGIC)
        put_uint32(buf, 0x04, ROOT_OFFSET)

        root_node = _U8Node()
        root_node.isDir = True
        nodes = [root_node]
        strings = bytearray(1)
        full_data = bytearray()
        paths = self.get_paths()

        for path in paths:
            data = self._files[path]
            node = _U8Node()
            node.isDir = data is None
            node.offName = len(strings)

            name = path.split("/")[-1]
            strings += (name + "\0").encode("latin-1")

            recursion = path.count("/")
            if recursion < 0:
                recursion = 0

            if node.isDir:
                node.off_data = recursion
                node.lenData = len(nodes)
                for sub_path in paths:
                    if sub_path[: len(path)] == path:
                        node.lenData += 1
            else:
                node.off_data = len(full_data)
                node.lenData = len(data)
                full_data += data + bytearray(align32(node.lenData) - node.lenData)

            nodes.append(node)

        len_nodes = NODE_SIZE * len(nodes) + len(strings)
        off_data = align32(ROOT_OFFSET + len_nodes)
        root_node.lenData = len(nodes)

        put_uint32(buf, 0x08, len_nodes)
        put_uint32(buf, 0x0C, off_data)

        for node in nodes:
            if not node.isDir:
                node.off_data += off_data
            buf += node.pack()

        buf += strings
        buf += bytearray(off_data - len_nodes - ROOT_OFFSET)
        buf += full_data

        return bytes(buf)

    def get_paths(self):
        return sorted(list(self._files.keys()))

    def get_file(self, path):
        if path in self._files:
            return self._files[path]
        else:
            return None

    def add_dir(self, path):
        self._files[path] = None

    def add_file(self, path, data):
        self._files[path] = data
