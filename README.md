# inFAMOUS native rebuild — public dossier ⚡

This public repository is the static, sanitized project record for the
BucketComps inFAMOUS native rebuild.

The implementation, verification evidence, and live runtime are maintained
outside this public projection. This repository must remain safe to clone and
publish in full: no game assets, ROM data, keys, raw evidence, private wiki
copies, credentials, or live telemetry.

## Public surfaces

- Default dossier URL after merge: <https://bucketcomps.github.io/infamous/>
- Eventual dossier URL: `https://decomp.deucebucket.com/infamous/`
- Proposed local-live URL: `https://live.decomp.deucebucket.com/infamous`

The custom domain and proposed live hostname are deliberately **not cut over**.
The live link is labeled as a hold everywhere it appears.

## Work locally

```sh
python3 scripts/check_site.py
python3 -m http.server 8080 --directory site
```

Then open <http://127.0.0.1:8080/>.

Pull requests validate but do not deploy. A merge to `main` deploys only the
`site/` artifact through GitHub Pages.
