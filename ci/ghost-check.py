#!/usr/bin/env python3
"""Ghost check: finds OVH resources that exist but are not in the Terraform state of core/.

`terraform plan` only sees what Terraform manages. A user, node pool or S3 key that
someone created in the console is invisible to it: a "ghost". This script lists what
really exists through the OVH API and compares it with `terraform show -json` of core/.

Usage:
    terraform -chdir=core show -json > core-state.json
    python ci/ghost-check.py core-state.json core/terraform.tfvars [--remediate]

With --remediate it also deletes the ghosts that are safe to remove automatically:
node pools, project users and S3 keys. Instances, buckets, registries, networks and
clusters are only reported: deleting those could lose data, a human decides.

Needs OVH_CLIENT_ID and OVH_CLIENT_SECRET (OAuth2 service account) in the environment.
Exit code 0 = no ghosts (left), 2 = ghosts found (and not all removed), 1 = error.
Writes a Markdown report to stdout.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://eu.api.ovh.com/1.0"
TOKEN_URL = "https://www.ovh.com/auth/oauth2/token"

# Created by FlowFactor's bootstrap, outside our code, and expected to exist.
BOOTSTRAP_USERS = {"achrona-tfstate"}
BOOTSTRAP_BUCKET_SUFFIX = "-tfstate"


def token():
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": os.environ["OVH_CLIENT_ID"],
        "client_secret": os.environ["OVH_CLIENT_SECRET"],
        "scope": "all",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=30) as r:
        return json.load(r)["access_token"]


def call(tok, path, method="GET", tries=5):
    """Call the OVH API with retries: it sometimes answers 500 for a moment."""
    req = urllib.request.Request(API + path, method=method,
                                 headers={"Authorization": "Bearer " + tok})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def state_resources(state_file):
    with open(state_file, encoding="utf-8") as f:
        state = json.load(f)
    resources = []

    def walk(module):
        resources.extend(module.get("resources", []))
        for child in module.get("child_modules", []):
            walk(child)

    walk(state.get("values", {}).get("root_module", {}))
    by_type = {}
    for r in resources:
        if r.get("mode") == "managed":
            by_type.setdefault(r["type"], []).append(r["values"])
    return by_type


def service_name(tfvars):
    with open(tfvars, encoding="utf-8") as f:
        m = re.search(r'^\s*service_name\s*=\s*"([^"]+)"', f.read(), re.M)
    return m.group(1)


def find_ghosts(tok, state, base):
    """Returns a list of (description, delete_path or None)."""
    ghosts = []

    # Users (OpenStack/S3 identities of the project)
    known_users = {str(u["id"]) for u in state.get("ovh_cloud_project_user", [])}
    users = call(tok, base + "/user")
    for u in users:
        if str(u["id"]) not in known_users and u["description"] not in BOOTSTRAP_USERS:
            roles = ", ".join(r["name"] for r in u.get("roles", []))
            ghosts.append((f"user `{u['description']}` (id {u['id']}, roles: {roles})",
                           f"{base}/user/{u['id']}"))

    # S3 keys of the users Terraform manages
    known_keys = {c["access_key_id"] for c in state.get("ovh_cloud_project_user_s3_credential", [])}
    for u in users:
        if str(u["id"]) not in known_users:
            continue
        for c in call(tok, f"{base}/user/{u['id']}/s3Credentials"):
            if c["access"] not in known_keys:
                ghosts.append((f"S3 key `{c['access'][:8]}…` on user `{u['description']}`",
                               f"{base}/user/{u['id']}/s3Credentials/{c['access']}"))

    # Kubernetes clusters and node pools
    known_kubes = {k["id"] for k in state.get("ovh_cloud_project_kube", [])}
    known_pools = {p["id"] for p in state.get("ovh_cloud_project_kube_nodepool", [])}
    pool_names = []
    for kube_id in call(tok, base + "/kube"):
        if kube_id not in known_kubes:
            ghosts.append((f"Kubernetes cluster `{kube_id}`", None))
            continue
        for p in call(tok, f"{base}/kube/{kube_id}/nodepool"):
            pool_names.append(p["name"])
            if p["id"] not in known_pools:
                ghosts.append((f"node pool `{p['name']}` ({p['currentNodes']}x {p['flavor']})",
                               f"{base}/kube/{kube_id}/nodepool/{p['id']}"))

    # Instances: only the nodes of the node pools may exist
    for i in call(tok, base + "/instance"):
        if not any(i["name"].startswith(n + "-node-") for n in pool_names):
            ghosts.append((f"instance `{i['name']}` ({i.get('planCode')})", None))

    # Buckets
    known_buckets = {b["name"] for b in state.get("ovh_cloud_storage_object_bucket", [])}
    for b in call(tok, f"{base}/region/GRA/storage"):
        if b["name"] not in known_buckets and not b["name"].endswith(BOOTSTRAP_BUCKET_SUFFIX):
            ghosts.append((f"bucket `{b['name']}`", None))

    # Container registries
    known_regs = {r["id"] for r in state.get("ovh_cloud_project_containerregistry", [])}
    for r in call(tok, base + "/containerRegistry"):
        if r["id"] not in known_regs:
            ghosts.append((f"container registry `{r['name']}`", None))

    # Private networks
    known_nets = {n["id"] for n in state.get("ovh_cloud_network_private_vrack", [])}
    for n in call(tok, base + "/network/private"):
        openstack_ids = {reg.get("openstackId") for reg in n.get("regions", [])}
        if not (openstack_ids & known_nets) and n["id"] not in known_nets:
            ghosts.append((f"private network `{n['name']}`", None))

    return ghosts


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    remediate = "--remediate" in sys.argv
    state = state_resources(args[0])
    base = f"/cloud/project/{service_name(args[1])}"
    tok = token()
    ghosts = find_ghosts(tok, state, base)

    if not ghosts:
        print("### Ghost resources\n\nGeen gevonden: alles in OVH staat in de Terraform-state.")
        return 0

    print("### Ghost resources (bestaan in OVH, niet in de Terraform-state van core/)\n")
    left = 0
    for desc, delete_path in ghosts:
        if remediate and delete_path:
            try:
                call(tok, delete_path, method="DELETE")
                print(f"- {desc}: **verwijderd**")
                continue
            except urllib.error.HTTPError as e:
                print(f"- {desc}: verwijderen faalde ({e.code})")
        elif delete_path:
            print(f"- {desc}")
        else:
            print(f"- {desc}: *niet automatisch verwijderd, mens beslist*")
        left += 1
    return 2 if left else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # report, but don't hide it as "no ghosts"
        print(f"### Ghost-check faalde\n\n`{type(e).__name__}: {e}`")
        sys.exit(1)
