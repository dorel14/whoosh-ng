import pytest

from whoosh.plugins.manager import AnalyzerPlugin, PluginManager, QueryRewritePlugin
from whoosh.query import Every


class DummyAnalyzer:
    def __call__(self, value, **kwargs):
        return iter([type("Token", (), {"text": value.upper()})()])


class UpperCaseAnalyzerPlugin(AnalyzerPlugin):
    name = "upper_case_analyzer"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_analyzer(self.name, DummyAnalyzer())


class PrefixRewritePlugin(QueryRewritePlugin):
    name = "prefix_rewrite"
    version = "1.0.0"

    def register(self, manager: PluginManager) -> None:
        manager.register_query_rewriter(self)

    def rewrite(self, query, searcher):
        if query.__class__.__name__ == "Term" and query.text and not query.text.startswith("prefix:"):
            from whoosh.query import Term
            return Term(query.fieldname, f"prefix:{query.text}")
        return query


def test_analyzer_plugin_registers_analyzer():
    manager = PluginManager()
    plugin = UpperCaseAnalyzerPlugin()
    manager.register(plugin)

    assert "upper_case_analyzer" in manager.list_analyzers()
    analyzer = manager.get_analyzer("upper_case_analyzer")
    tokens = list(analyzer("hello"))
    assert tokens[0].text == "HELLO"


def test_query_rewrite_plugin_rewrites_query():
    manager = PluginManager()
    plugin = PrefixRewritePlugin()
    manager.register(plugin)

    rewriter = manager.get_query_rewriter("prefix_rewrite")
    from whoosh.query import Term

    query = Term("content", "hello")
    rewritten = rewriter.rewrite(query, searcher=None)
    assert rewritten.text == "prefix:hello"


def test_plugin_manager_lists_plugins():
    manager = PluginManager()
    manager.register(UpperCaseAnalyzerPlugin())
    manager.register(PrefixRewritePlugin())

    assert set(manager.list_plugins()) == {"upper_case_analyzer", "prefix_rewrite"}
    assert manager.list_analyzers() == ["upper_case_analyzer"]
    assert manager.list_query_rewriters() == ["prefix_rewrite"]
