# data-factory

Automated pipeline that **collects** data, **processes** it into clean validated tables and **publishes**
it as packaged, licensed data products ready for data marketplaces.

- User guide (install, run, create datasets): [`docs/user-guide.md`](docs/user-guide.md)
- Technical guide (internals, extending, testing): [`docs/technical-guide.md`](docs/technical-guide.md)
- Architecture: [`docs/architecture.md`](docs/architecture.md)
- Contributor & AI-agent rules: [`AGENTS.md`](AGENTS.md)

```bash
make install   # requires uv
make check
uv run datafactory run wb-macro-indicators   # build the World Bank product
```
