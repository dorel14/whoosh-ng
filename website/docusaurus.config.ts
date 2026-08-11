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
          to: '/',
          label: 'Docs',
          position: 'left',
        },
        {
          to: '/api/overview',
          label: 'API',
          position: 'left',
        },
        {
          to: '/core/changelog',
          label: 'Changelog',
          position: 'left',
        },
        {
          to: 'https://github.com/users/dorel14/projects/2/views/2?sliceBy%5BcolumnId%5D=Milestone',
          label: 'Roadmap',
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
          title: 'LLM Context',
          items: [
            { label: 'llms.txt', to: '/llms.txt' },
            { label: 'llms-full.txt', to: '/llms-full.txt' },
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
      copyright: 'Whoosh-NG Documentation v4.3.0 | Last updated: 2026-08-10',
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
    },
    // Force dark theme as default — visitors start in dark mode.
    // They can still toggle to light mode via the navbar button.
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
  },

  onBrokenLinks: 'warn',
  onBrokenAnchors: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },
};

export default config;
