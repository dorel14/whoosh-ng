import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  // Full site sidebar — shown on homepage and pages without a scoped sidebar
  docs: {
    Core: [
      {
        type: 'doc',
        id: 'index',
        label: 'Overview',
      },
      {type: 'doc', id: 'core/index', label: 'Core'},
      'core/quickstart',
      'core/installation',
      {
        type: 'category',
        label: 'Classic Features',
        items: [
          'core/core-concepts',
          'core/indexing',
          'core/searching',
          'core/schema',
          'core/query',
          'core/backends',
          'core/dates',
          'core/nested',
          'core/sorting',
          'core/auto-indexing',
        ],
      },
      {
        type: 'category',
        label: 'Reference',
        items: [
          'core/glossary',
          'core/migration',
          'core/changelog',
          'core/legacy-cleanup',
          'core/translation-status',
        ],
      },
    ],
    Modern: [
      {type: 'doc', id: 'modern/index', label: 'Modern'},
      'modern/middleware',
      'modern/middleware-pipeline',
      'modern/plugins',
      'modern/plugins-advanced',
      'modern/autocomplete',
      'modern/autocomplete-providers',
      'modern/vector',
      'modern/modern-indexing',
      'modern/monitoring',
      'modern/performance',
      'modern/linguistics',
      'modern/stemming',
      'modern/stemming-providers',
      'modern/ngrams',
      'modern/storage-providers',
      'modern/provider-integration',
    ],
  },
  // Dedicated sidebar for Changelog — shows ONLY the changelog entry
  // for quick version navigation, not the full Core site tree.
  changelogSidebar: {
    Changelog: [
      {
        type: 'doc',
        id: 'core/changelog',
        label: 'Changelog',
      },
    ],
  },
  // Dedicated sidebar for API section
  apiSidebar: {
    'API Reference': [
      'api/overview',
      'api/reference',
      {
        type: 'category',
        label: 'Core API',
        items: [
          'api/fields',
          'api/analysis',
          'api/highlight',
          'api/spelling',
          'api/sorting',
          'api/collectors',
          'api/reading',
          'api/matching',
          'api/codecs',
          'api/formats',
          'api/columns',
          'api/idsets',
          'api/automata',
          'api/classify',
          'api/lang',
        ],
      },
      {
        type: 'category',
        label: 'Modern API',
        items: [
          'api/writing',
          'api/searching',
          'api/query',
          'api/events',
          'api/middleware',
          'api/plugins',
          'api/backends',
          'api/filedb_storage',
          'api/modern',
        ],
      },
    ],
  },
  // Dedicated sidebar for Examples section
  examplesSidebar: {
    Examples: [
      'examples/basic-indexing',
      'examples/search',
      'examples/search-models',
      'examples/fastapi-search',
      'examples/middleware',
      'examples/middleware-pipeline',
      'examples/movie-search',
      'examples/plugin-dev',
      'examples/data-sources',
      'examples/schema-discovery',
      'examples/facets',
      'examples/validation',
      'examples/search-view',
      'examples/autocomplete',
      'examples/vector-search',
    ],
  },
};

export default sidebars;
