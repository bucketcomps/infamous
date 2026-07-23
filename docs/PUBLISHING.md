# Publishing

The custom GitHub Pages workflow:

1. validates every relevant pull request and push;
2. uploads only `site/`;
3. grants deployment permissions only to the deploy job;
4. skips deployment on pull requests; and
5. pins every action to a full commit SHA.

There is intentionally no `CNAME` file. Custom-domain work belongs to the
organization Pages cutover and is not part of this dossier PR.

Official references:

- [Configuring a Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Using custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
