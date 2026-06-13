from whoosh.registry.base import Registry

StorageRegistry = Registry("storage")
AnalyzerRegistry = Registry("analyzer")
RankingRegistry = Registry("ranking")
SuggestRegistry = Registry("suggest")
VectorRegistry = Registry("vector")
AutocompleteRegistry = Registry("autocomplete")

__all__ = [
    "Registry",
    "StorageRegistry",
    "AnalyzerRegistry",
    "RankingRegistry",
    "SuggestRegistry",
    "VectorRegistry",
    "AutocompleteRegistry",
]
