import type {Config} from '@docusaurus/types';
import {themes as prismThemes} from 'prism-react-renderer';

const config: Config = {
  title: 'Whoosh-NG Documentation',
  tagline: 'Pure-Python full-text indexing and search library, modernized for 2025+',
  favicon: 'favicon.ico',

  url: 'https://dorel14.github.io',
  baseUrl: '/whoosh-ng/',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr'],
  },

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/dorel14/whoosh-ng/tree/master/website/docs',
        },
        blog: false,
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'Whoosh-NG',
      logo: {
        alt: 'Whoosh-NG Logo',
        src: 'img/logo.png',
      },
      items: [
        {
          to: '/core/quickstart',
          label: 'Core',
          position: 'left',
        },
        {
          to: '/modern/middleware',
          label: 'Modern',
          position: 'left',
        },
        {
          to: '/api/overview',
          label: 'API',
          position: 'left',
        },
        {
          to: '/examples/basic-indexing',
          label: 'Examples',
          position: 'left',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/dorel14/whoosh-ng',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Core', to: '/core/quickstart' },
            { label: 'Modern', to: '/modern/middleware' },
            { label: 'API Reference', to: '/api/overview' },
            { label: 'Examples', to: '/examples/basic-indexing' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub', href: 'https://github.com/dorel14/whoosh-ng' },
            { label: 'PyPI', href: 'https://pypi.org/project/whoosh-ng/' },
          ],
        },
      ],
      copyright: 'Whoosh-NG Documentation v4.0.1 | Last updated: 2026-08-07',
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
    },
  },

  onBrokenLinks: 'warn',
  onBrokenAnchors: 'throw',
  onBrokenMarkdownLinks: 'warn',
};

export default config;
