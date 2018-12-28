# coding: utf-8
from __future__ import unicode_literals, print_function, division, absolute_import
from lingvoreader.tools import int2unichr

__author__ = 'svolkov'


# info from ArticleHeading.cpp
# Not implemented yet!!
#
#      Unsorted parts
#
# Each characted in a LSD heading has a flag indicating if it's 'sorted' or 'unsorted'.
# The unsorted characters aren't used in sortings and searching. Basically they become
# transparent for the indexing mechanism and only visible while presented to the user
# together with an article. Let's annotate each character with an 's' or 'u' to indicate
# this distinction.
#
# In the DSL format curly brackets are used to denote the sortedness of a heading's part.
#
# The heading 'Some{thing}' would be encoded as
#
#   Something
#   ssssuuuuu
#
# And it's name would be just 'Some', while its extended name would be 'Something'
# There can be any number of unsorted characters in a heading. At any position.
#
# To correctly decompile an LSD heading (where each character is either sorted or unsorted)
# to a DSL heading, it is required to group adjacent characters in groups by their
# sortedness, and then enclose each such group in parentheses. This process is rather
# straightforward. The special case to look for is the slash (/), which is encoded
# as an unsorted character, but is used to escape the subsequent characted (either sorted
# or unsorted) and thus requires a special handling.
#
#      Optional parts (variants)
#
# The DSL format has a mechanism for generating several headings with optional parts
# out of a single heading. By enclosing a part of a heading in parentheses, it is possible
# to generate all possible combinations of the heading.
#
# The heading 'aa(bb)cc' would be expanded into two different headings
#
#   aa{(bb)}cc  and  aa{(}bb{)}cc
#   ss uuuu ss       ss u ss u ss
#
# For more such parts, more headings would be generated. It is 2 headings for 1 part,
# 4 headings for 2 parts, 9 for 3 and so on.
#
# There exists a pattern which helps to combine two headings produced with the variant
# encoding. The pattern looks like this 'u(' denotes an unsorted parenthesis):
#
#   (A)  ??? u(   u*n u) ???   ->   ??? s( s|u*n s) ???
#   (B)  ??? u( s|u*n u) ???
#
# An optional part can contain an unsorted part as well, so this pattern allow for a
# combination of sorted/unsorted parts in an optional part (denoted as 's|u*n').
#
# This pattern becomes insufficient in the presence of spaces, adjacent to the
# parentheses. Here are two examples of such headings (the upper case is used
# to denote spaces):
#
#   abc (123)
#
#   abc{ (123)}    and   abc {(}123{)}
#   sss Uuuuuu           sssS u sss u
#
#   bbb (123) z
#
#   bbb {(123) }z  and   bbb {(}123{)} z
#   sssS uuuuuU s        sssS u sss u Ss
#
# Another two patterns account for these special cases.
#
#   (C) ??? Uu(   u*n u)  ->  ??? Ss( s|u*n s)
#   (D) ??? Su( s|u*n u)
#
#   (E) ??? Su(   u*n u)U ???  ->  ??? Ss( s|u*n s)S ???
#   (F) ??? Su( s|u*n u)S ???
#
# The headings that can't be collapsed using one of these three rules are left as is.
#
#
class CharInfo:
    def __init__(self):
        self.sorted = False
        self.escaped = False
        self.chr = ""

    # add equal test


class Heading:
    def __init__(self):
        self.text = ""
        self.extensions = []

    @property
    def ext_text(self):
        if len(self.extensions) == 0:
            return self.text
        res = self.text
        offset = 0
        for idx, ext in self.extensions:
            add_braces = ext != u"\\"
            if add_braces:
                ext = u"{" + ext + u"}"

            res = res[:idx + offset] + ext + res[idx + offset:]
            if add_braces:
                offset += 2
        return res


class ArticleHeading:
    def __init__(self):
        # may by many heading for single article
        self.headings = []
        self.reference = 0
        # refernce for next arcticle, used in the x6 for encoding
        self.next_reference = 0

    def read(self, lsd_decoder, bstr, known_prefix):
        h = Heading()
        prefix_len = lsd_decoder.decode_prefix_len()
        postfix_len = lsd_decoder.decode_postfix_len()
        h.text = known_prefix[:prefix_len]
        h.text += lsd_decoder.decode_heading(postfix_len)
        self.reference = lsd_decoder.read_reference2()
        if bstr.read_bit():
            # additional not visible formatting item in header
            # join multisymbols item
            ext_length = bstr.read_bits(8)
            if ext_length != 0:
                ext = ""
                first_idx = prev_idx = 0
                for i in range(ext_length):
                    idx = bstr.read_bits(8)
                    char = int2unichr(bstr.read_bits(16))
                    if ext == "":
                        ext += char
                        first_idx = prev_idx = idx
                    else:
                        if prev_idx + 1 == idx:
                            # join item with sequence idx
                            ext += char
                            prev_idx = idx
                        else:
                            # other item
                            h.extensions.append((first_idx, ext))
                            ext = char
                            first_idx = prev_idx = idx
                # add last item
                h.extensions.append((first_idx, ext))
        self.headings.append(h)
        return h.text

    def merge(self, heading):
        for h in heading.headings:
            # print("merge: %s" % h.ext_text)
            self.headings.append(h)

    def get_first(self):
        return self.headings[0]

    def get_first_ext_text(self):
        return self.headings[0].ext_text

    @property
    def simple(self):
        return len(self.headings) == 1

    def dump(self):
        print("%s: %d - %d" % (self.get_first().text, self.reference, self.next_reference))


class ArticleHeadingList(list):
    def __init__(self):
        super(ArticleHeadingList, self).__init__()
        self.appended = 0
        self.references = {}

    def append(self, item):
        self.appended += 1
        # append if item.reference not exists
        ref = item.reference
        if ref in self.references:
            self.references[ref].merge(item)
        else:
            self.references[ref] = item
            # if not first then update next_reference in the previous item
            if len(self) > 0:
                self[-1].next_reference = ref
            super(ArticleHeadingList, self).append(item)
