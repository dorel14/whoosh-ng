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
"""Faceting and sorting of search results.

This package is a refactored version of the former monolithic
``whoosh.sorting`` module. The public API (class and function names) is
unchanged: importing from ``whoosh.sorting`` continues to work exactly as
before.
"""

from whoosh.sorting.facet import (
    Best,
    Categorizer,
    ColumnCategorizer,
    Count,
    DateRangeFacet,
    FacetMap,
    Facets,
    FacetType,
    FieldFacet,
    FunctionFacet,
    MultiFacet,
    OrderedList,
    OverlappingCategorizer,
    PostingCategorizer,
    QueryFacet,
    RangeFacet,
    ReversedColumnCategorizer,
    ScoreFacet,
    StoredFieldFacet,
    TranslateFacet,
    UnorderedList,
)
from whoosh.sorting.sort import add_sortable

__all__ = (
    "FacetType",
    "Categorizer",
    "FieldFacet",
    "ColumnCategorizer",
    "ReversedColumnCategorizer",
    "OverlappingCategorizer",
    "PostingCategorizer",
    "QueryFacet",
    "RangeFacet",
    "DateRangeFacet",
    "ScoreFacet",
    "FunctionFacet",
    "TranslateFacet",
    "StoredFieldFacet",
    "MultiFacet",
    "Facets",
    "FacetMap",
    "OrderedList",
    "UnorderedList",
    "Count",
    "Best",
    "add_sortable",
)
