# Copyright 2007 Matt Chaput. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY MATT CHAPUT ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL MATT CHAPUT OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Matt Chaput.

import codecs
import re
from re import Pattern

utf8encode = codecs.getencoder("utf-8")
utf8decode = codecs.getdecoder("utf-8")

# Note: these functions return a tuple of (text, length), so when you call
# them, you have to add [0] on the end, e.g. str = utf8encode(unicode)[0]


def byte(num: int) -> bytes:
    return bytes((num,))


def first_diff(a: bytes | str, b: bytes | str) -> int:
    """
    Returns the position of the first differing character in the sequences a
    and b. For example, first_diff(b'render', b'rending') == 4. This function
    limits the return value to 255 so the difference can be encoded in a single
    byte.
    """
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")

    i = 0
    while i <= 255 and i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    return i


def prefix_encode(a: bytes | str, b: bytes | str) -> bytes:
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    i = first_diff(a, b)
    return byte(i) + b[i:]


def prefix_encode_all(s: bytes | str) -> bytes:
    """Encode a string or bytes as a sequence of prefix-encoded bytes.

    This is a legacy Python 2 prefix codec function kept for backward
    compatibility with code that migrates from whoosh to whoosh-ng.
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    result: list[bytes] = []
    prev: bytes = b""
    for ch in s:
        encoded = prefix_encode(prev, bytes((ch,)))
        result.append(encoded)
        prev = bytes((ch,))
    return b"".join(result)


def prefix_decode_all(s: bytes | str) -> bytes:
    """Decode a prefix-encoded byte sequence back to bytes.

    This is a legacy Python 2 prefix codec function kept for backward
    compatibility with code that migrates from whoosh to whoosh-ng.
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    result: list[bytes] = []
    i = 0
    while i < len(s):
        diff_pos = s[i]
        i += 1
        char_bytes = s[i : i + diff_pos]
        result.append(char_bytes)
        i += diff_pos
    return b"".join(result)


def natural_key(s: bytes | str) -> bytes:
    """Generate a natural sort key for a string or bytes.

    This is a legacy Python 2 prefix codec function kept for backward
    compatibility with code that migrates from whoosh to whoosh-ng.
    """
    if isinstance(s, str):
        s = s.encode("utf-8")
    parts: list[bytes] = []
    num_buf: bytes = b""
    for ch in s:
        if 48 <= ch <= 57:
            num_buf += bytes((ch,))
        else:
            if num_buf:
                parts.append(num_buf)
                num_buf = b""
            parts.append(bytes((ch,)))
    if num_buf:
        parts.append(num_buf)
    return b"".join(parts)


# Regular expression functions


def rcompile(pattern: str | Pattern[str], flags: int = 0, verbose: bool = False) -> Pattern[str]:
    """A wrapper for re.compile that checks whether "pattern" is a regex object
    or a string to be compiled, and automatically adds the re.UNICODE flag.
    """

    if not isinstance(pattern, str):
        # If it's not a string, assume it's already a compiled pattern
        return pattern
    if verbose:
        flags |= re.VERBOSE
    return re.compile(pattern, re.UNICODE | flags)
    """A wrapper for re.compile that checks whether "pattern" is a regex object
    or a string to be compiled, and automatically adds the re.UNICODE flag.
    """

    if not isinstance(pattern, str):
        # If it's not a string, assume it's already a compiled pattern
        return pattern
    if verbose:
        flags |= re.VERBOSE
    return re.compile(pattern, re.UNICODE | flags)
