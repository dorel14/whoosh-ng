import struct

from whoosh import fields, formats
from whoosh.filedb.filepostings import FilePostingReader, FilePostingWriter
from whoosh.util.testing import TempStorage


def test_huge_postfile():
    with TempStorage("hugeindex") as st:
        pf = st.create_file("test.pst")

        gb5 = 5 * 1024 * 1024 * 1024
        pf.seek(gb5)
        pf.write(b"\x00\x00\x00\x00")
        assert pf.tell() == gb5 + 4

        schema = fields.Schema(text=fields.KEYWORD(scorable=False))
        fpw = FilePostingWriter(schema, pf)
        offset = fpw.start(0)
        for i in range(10):
            fpw.write(i, struct.pack("!I", i))
        posttotal = fpw.finish()
        assert posttotal == 10
        fpw.close()

        pf = st.open_file("test.pst")
        pfr = FilePostingReader(pf, offset, schema[0].format)
        i = 0
        while pfr.is_active():
            assert pfr.id() == i
            assert pfr.weight() == float(i)
            assert pfr.value() == struct.pack("!I", i)
            pfr.next()
            i += 1
        pf.close()
