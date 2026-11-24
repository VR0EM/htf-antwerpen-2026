#!/bin/sh
# Serves the grimoire over HTTP. Creates it from the genesis pages on first
# start.
set -eu
export HOME=/tmp
git config --global safe.directory '*'
git config --global init.defaultBranch main
REPO=/srv/git/realm.git
if [ ! -f "$REPO/HEAD" ]; then
  echo "[grimoire] writing the genesis"
  git init --bare -q "$REPO"
  work=$(mktemp -d)
  cp -rL /genesis/pages/. "$work/"
  cd "$work"
  git init -q
  git add -A
  GIT_AUTHOR_NAME="Guild of Architects" GIT_AUTHOR_EMAIL="architects@guild.achrona.realm" \
  GIT_COMMITTER_NAME="Guild of Architects" GIT_COMMITTER_EMAIL="architects@guild.achrona.realm" \
    git commit -q -m "Genesis: the Seer awakens"
  git push -q "$REPO" HEAD:main
  cd / && rm -rf "$work"
fi
# HTF L3 (#57): om 13:39 werd een post-receive-hook geplant die 75 s na elke push
# een vergiftigde persona terugzette. Hooks staan niet in Git, dus revert helpt niet.
# Bij elke start: enkel onze update-hook, geen andere hooks, geen eigen hooksPath.
find "$REPO/hooks" -mindepth 1 -maxdepth 1 ! -name '*.sample' -exec rm -rf {} +
git -C "$REPO" config --unset-all core.hooksPath 2>/dev/null || true
cp /genesis/update-hook "$REPO/hooks/update"
chmod +x "$REPO/hooks/update"
echo "[grimoire] hooks: $(ls "$REPO/hooks" | grep -v '\.sample$' | tr '\n' ' ')"
git -C "$REPO" config http.receivepack true
exec python3 -u /genesis/serve.py
