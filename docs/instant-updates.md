# Instant profile updates

The profile refreshes every 10 minutes on its own. To refresh the moment you push to any repo,
add this file as `.github/workflows/notify-profile.yml` to that repo, and create a fine-grained
token (Settings > Developer settings > Personal access tokens) with **Actions: read and write**
on `UzairBaig991/UzairBaig991`. Save it in the repo's secrets as `PROFILE_TOKEN`.

```yaml
name: Notify profile
on: [push]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -s -X POST \
            -H "Authorization: Bearer ${{ secrets.PROFILE_TOKEN }}" \
            -H "Accept: application/vnd.github+json" \
            https://api.github.com/repos/UzairBaig991/UzairBaig991/dispatches \
            -d '{"event_type":"repo-updated"}'
```
