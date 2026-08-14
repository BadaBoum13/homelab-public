#!/usr/bin/env python3
"""
Driver for the homelab-k3s cluster.

Two halves:
  * OFFLINE  - parse every ArgoCD Application in app/, reproduce locally what
               ArgoCD would render (helm template / raw manifests), validate it.
               Needs no cluster.
  * LIVE     - read-only inspection of the running cluster + server-side dry-run
               diffs. Needs KUBECONFIG.

Nothing here mutates the cluster. `diff` uses a server-side dry-run, which is
read-only; there is deliberately no `apply` subcommand -- prod is reconciled by
ArgoCD from git, not from a laptop.

Run from the repo root:  .claude/skills/run-homelab-k3s/driver.py <cmd>
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import shutil
import subprocess
import sys

import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
KUBECONFIG = os.environ.get("KUBECONFIG") or os.path.expanduser("~/.kube/config-k3s-prod")
OUT = os.environ.get("DRIVER_OUT", "/tmp/homelab-render")

# The app-of-apps only picks up these filenames; match it exactly.
APP_FILES = ("argocd-helm.yaml", "argocd-helm-crds.yaml", "argocd-config.yaml")

C = {"r": "\033[31m", "g": "\033[32m", "y": "\033[33m", "b": "\033[34m",
     "d": "\033[2m", "0": "\033[0m"}
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C = dict.fromkeys(C, "")


def color(s, c):
    return f"{C[c]}{s}{C['0']}"


def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    return subprocess.run(cmd, **kw)


def kube(args, timeout=60):
    env = dict(os.environ, KUBECONFIG=KUBECONFIG)
    return run(["kubectl", *args], env=env, timeout=timeout)


def need_cluster():
    if not os.path.exists(KUBECONFIG):
        sys.exit(f"no kubeconfig at {KUBECONFIG} (set KUBECONFIG)")
    p = kube(["get", "--raw", "/version"], timeout=25)
    if p.returncode != 0:
        sys.exit(f"cluster unreachable via {KUBECONFIG}\n{p.stderr.strip()}\n"
                 "The homelab node is LAN-only; check the link is up.")


# --------------------------------------------------------------------------
# discovery
# --------------------------------------------------------------------------
def load_apps(include_deprecated=False):
    """Every ArgoCD Application in app/, as (name, spec, file) records."""
    apps = []
    for path in sorted(glob.glob(os.path.join(REPO, "app", "**", "*.yaml"), recursive=True)) + \
                sorted(glob.glob(os.path.join(REPO, "app", "*.yaml"))):
        rel = os.path.relpath(path, REPO)
        if not include_deprecated and rel.startswith("app/deprecated/"):
            continue
        base = os.path.basename(path)
        if base not in APP_FILES and base != "argocd-bootstrap.yaml":
            continue
        try:
            docs = [d for d in yaml.safe_load_all(open(path)) if d]
        except yaml.YAMLError as e:
            print(color(f"  {rel}: YAML parse error: {e}", "r"))
            continue
        for d in docs:
            if d.get("kind") == "Application":
                apps.append((d["metadata"]["name"], d["spec"], rel, d["metadata"]))
    # de-dup on name, keep first
    seen, out = set(), []
    for a in apps:
        if a[0] in seen:
            continue
        seen.add(a[0])
        out.append(a)
    return sorted(out, key=lambda a: a[0])


def resolve(target, apps):
    """Accept an app name, a dir path, or a substring."""
    names = {a[0]: a for a in apps}
    if target in names:
        return names[target]
    t = target.rstrip("/")
    hits = [a for a in apps if a[2].startswith(t + "/") or os.path.dirname(a[2]) == t]
    if hits:
        # a directory usually holds both argocd-helm.yaml and argocd-config.yaml;
        # the helm one is the app, so prefer it instead of calling this ambiguous
        main = [a for a in hits if os.path.basename(a[2]) == "argocd-helm.yaml"]
        if main:
            return main[0]
    else:
        hits = [a for a in apps if target in a[0]]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"no app matches {target!r}. Try: {', '.join(sorted(names))}")
    sys.exit(f"{target!r} is ambiguous: {', '.join(a[0] for a in hits)}")


def wave(meta):
    return meta.get("annotations", {}).get("argocd.argoproj.io/sync-wave", "-")


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------
def chart_source(spec):
    """The helm source of an Application, if it has one."""
    for src in spec.get("sources", [spec.get("source", {})]):
        if "chart" in src:
            return src
    return None


def values_files(src):
    """Resolve valueFiles.

    Only `$values/<path>` entries point at this repo (the `ref: values` source).
    A bare relative path resolves against the *chart's* own root, so helm picks
    it up on its own and a repo-local file of the same name is simply ignored --
    openbao is in exactly that state. Return those separately as warnings.
    """
    out, warn = [], []
    for vf in src.get("helm", {}).get("valueFiles", []):
        if vf.startswith("$values/"):
            out.append(os.path.join(REPO, vf[len("$values/"):]))
        else:
            warn.append(vf)
    return out, warn


def brace_expand(pat):
    """fnmatch has no {a,b} alternation; ArgoCD's include patterns use it."""
    m = re.search(r"\{([^{}]*)\}", pat)
    if not m:
        return [pat]
    out = []
    for opt in m.group(1).split(","):
        out += brace_expand(pat[:m.start()] + opt + pat[m.end():])
    return out


def matches(rel, name, pat):
    for p in brace_expand(pat):
        # ArgoCD matches the path relative to source.path, and '**' spans dirs
        if fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p):
            return True
        if p.startswith("**/") and fnmatch.fnmatch(rel, p[3:]):
            return True
    return False


def strip_test_hooks(text):
    """Drop `helm.sh/hook: test` resources.

    They are never part of a sync, and grafana's test pod references a
    ServiceAccount that does not exist -- which makes `kubectl diff` bail out
    with a Forbidden error before it reaches the real objects.
    """
    keep = []
    for d in yaml.safe_load_all(text):
        if not d:
            continue
        hook = (d.get("metadata", {}).get("annotations") or {}).get("helm.sh/hook", "")
        if "test" in hook:
            continue
        keep.append(yaml.safe_dump(d, default_flow_style=False))
    return "---\n" + "---\n".join(keep)


def render_app(name, spec, rel, meta):
    """Reproduce what ArgoCD renders. Returns (ok, manifest_text, warnings).

    `rel` and `meta` are unused today but every call site unpacks the same
    4-tuple from load_apps(), so they stay in the signature.
    """
    ns = spec.get("destination", {}).get("namespace", "default")
    src = chart_source(spec)
    warns = []

    if src:
        repo = src["repoURL"]
        if repo.startswith("oci://"):
            # OCI registries are addressed as a single ref, not --repo/chart
            cmd = ["helm", "template", name, f"{repo.rstrip('/')}/{src['chart']}"]
        else:
            cmd = ["helm", "template", name, src["chart"], "--repo", repo]
        cmd += ["--namespace", ns, "--include-crds"]
        tr = src.get("targetRevision")
        # "*" means "latest" to ArgoCD; helm wants the flag omitted.
        if tr and tr != "*":
            cmd += ["--version", tr]
        vfs, bare = values_files(src)
        for vf in bare:
            warns.append(f"valueFiles {vf!r} has no $values/ prefix -> resolved "
                         f"against the chart, NOT this repo (repo values ignored)")
        for vf in vfs:
            if not os.path.exists(vf):
                alt = [e for e in (".yaml", ".yml")
                       if os.path.exists(os.path.splitext(vf)[0] + e)]
                hint = f" (did you mean {os.path.basename(os.path.splitext(vf)[0] + alt[0])}?)" if alt else ""
                return False, f"values file missing: {os.path.relpath(vf, REPO)}{hint}", warns
            cmd += ["-f", vf]
        inline = src.get("helm", {}).get("values")
        if inline:
            tmp = os.path.join(OUT, f"{name}-inline-values.yaml")
            os.makedirs(OUT, exist_ok=True)
            open(tmp, "w").write(inline)
            cmd += ["-f", tmp]
        p = run(cmd, timeout=180)
        if p.returncode != 0:
            return False, p.stderr.strip(), warns
        return True, strip_test_hooks(p.stdout), warns

    # raw-manifest Application: source.path + directory.include
    s = spec.get("source", {})
    path = s.get("path")
    if not path:
        return False, "Application has neither a chart nor a source.path", warns
    d = os.path.join(REPO, path)
    if not os.path.isdir(d):
        return False, f"source.path does not exist in repo: {path}", warns
    inc = s.get("directory", {}).get("include", "*")
    recurse = s.get("directory", {}).get("recurse", False)
    exclude = s.get("directory", {}).get("exclude")

    files = []
    walk = os.walk(d) if recurse else [(d, [], sorted(os.listdir(d)))]
    for root, _, names in walk:
        for n in sorted(names):
            fp = os.path.join(root, n)
            r = os.path.relpath(fp, d)
            if not os.path.isfile(fp):
                # include can name a bare subdirectory (cert-manager: include: crd)
                if os.path.isdir(fp) and matches(r, n, inc):
                    files += sorted(glob.glob(os.path.join(fp, "*.y*ml")))
                continue
            if matches(r, n, inc) and not (exclude and matches(r, n, exclude)):
                files.append(fp)
    if not files:
        # ArgoCD does the same thing and reports Synced/Healthy with 0 resources
        return True, "", warns + [
            f"include {inc!r} (recurse={recurse}) matched NO files under {path} -- "
            f"this app renders 0 objects and manages nothing"]
    parts = []
    for f in sorted(set(files)):
        parts.append(f"# source: {os.path.relpath(f, REPO)}\n" + open(f).read())
    return True, "\n---\n".join(parts), warns


def cmd_render(a):
    apps = load_apps(a.deprecated)
    targets = apps if a.all else [resolve(a.app, apps)]
    os.makedirs(OUT, exist_ok=True)
    fails = 0
    for name, spec, rel, meta in targets:
        ok, text, warns = render_app(name, spec, rel, meta)
        if not ok:
            fails += 1
            print(f"{color('FAIL', 'r')} {name:32} {text.splitlines()[0] if text else ''}")
            continue
        dest = os.path.join(OUT, f"{name}.yaml")
        open(dest, "w").write(text)
        n = sum(1 for d in yaml.safe_load_all(text) if d)
        if a.all:
            tag = color(' ok ', 'g') if n else color('EMPTY', 'y')
            print(f"{tag} {name:32} {n:4} objects  -> {dest}")
        else:
            sys.stdout.write(text)
            print(f"\n{color(f'# {n} objects -> {dest}', 'd')}", file=sys.stderr)
        for w in warns:
            print(f"     {color('warn: ' + w, 'y')}")
    if a.all:
        print(f"\n{len(targets) - fails}/{len(targets)} rendered into {OUT}")
    return 1 if fails else 0


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------
def check_objects(text):
    """Pure-python structural validation -- no kubectl, no cluster."""
    errs, n = [], 0
    for i, d in enumerate(yaml.safe_load_all(text)):
        if not d:
            continue
        n += 1
        if not isinstance(d, dict):
            errs.append(f"doc {i}: not a mapping")
            continue
        for f in ("apiVersion", "kind"):
            if not d.get(f):
                errs.append(f"doc {i}: missing {f}")
        if not (d.get("metadata") or {}).get("name") and d.get("kind") != "List":
            errs.append(f"doc {i} ({d.get('kind')}): missing metadata.name")
    return n, errs


def cmd_lint(a):
    """Render everything, then validate each object."""
    apps = load_apps(a.deprecated)
    os.makedirs(OUT, exist_ok=True)
    if a.cluster:
        need_cluster()
    bad = 0
    for name, spec, rel, meta in apps:
        ok, text, warns = render_app(name, spec, rel, meta)
        if not ok:
            bad += 1
            print(f"{color('RENDER', 'r')} {name:32} {text.splitlines()[0] if text else ''}")
            continue
        if not text.strip():
            print(f"{color(' EMPTY', 'y')} {name:32}    0 objects")
            for w in warns:
                print(f"       {color(w, 'y')}")
            continue
        dest = os.path.join(OUT, f"{name}.yaml")
        open(dest, "w").write(text)

        if a.cluster:
            # server-side dry-run: real schema + admission validation, no writes
            p = kube(["apply", "--dry-run=server", "-f", dest, "-o", "name"], timeout=180)
            ok2, detail = p.returncode == 0, p.stderr.strip().splitlines()
            objs = len([l for l in p.stdout.splitlines() if l.strip()])
        else:
            objs, errs = check_objects(text)
            ok2, detail = not errs, errs

        if ok2:
            print(f"{color('  ok  ', 'g')} {name:32} {objs:4} objects")
        else:
            bad += 1
            print(f"{color('INVALID', 'r')} {name:32} {detail[0] if detail else ''}")
            for l in detail[1:4]:
                print(f"        {l}")
        for w in warns:
            print(f"       {color('warn: ' + w, 'y')}")
    print(f"\n{len(apps) - bad}/{len(apps)} apps valid")
    return 1 if bad else 0


# --------------------------------------------------------------------------
# live cluster
# --------------------------------------------------------------------------
def cmd_status(a):
    need_cluster()
    print(color("== node ==", "b"))
    print(kube(["get", "nodes", "-o", "wide"]).stdout.rstrip())

    print(color("\n== argocd applications ==", "b"))
    p = kube(["get", "applications", "-A", "-o", "json"])
    if p.returncode == 0:
        for it in json.loads(p.stdout)["items"]:
            st = it.get("status", {})
            sync = st.get("sync", {}).get("status", "?")
            health = st.get("health", {}).get("status", "?")
            c = "g" if sync == "Synced" else ("y" if sync == "OutOfSync" else "d")
            hc = "g" if health == "Healthy" else "y"
            print(f"  {it['metadata']['name']:32} {color(sync, c):22} {color(health, hc)}")

    print(color("\n== pods not Running/Succeeded ==", "b"))
    p = kube(["get", "pods", "-A", "-o", "json"])
    rows = []
    for it in json.loads(p.stdout)["items"]:
        ph = it["status"].get("phase")
        if ph in ("Running", "Succeeded"):
            continue
        rows.append(f"  {it['metadata']['namespace']:16} {it['metadata']['name']:44} {ph}")
    print("\n".join(rows) if rows else color("  (all healthy)", "g"))

    print(color("\n== ingress ==", "b"))
    print("\n".join("  " + l for l in kube(["get", "ingress", "-A"]).stdout.rstrip().splitlines()))

    print(color("\n== certificates ==", "b"))
    p = kube(["get", "certificates", "-A", "-o",
              "custom-columns=NS:.metadata.namespace,NAME:.metadata.name,"
              "READY:.status.conditions[0].status,EXPIRY:.status.notAfter"])
    print("\n".join("  " + l for l in p.stdout.rstrip().splitlines()) if p.returncode == 0
          else color("  (no cert-manager CRDs)", "d"))

    print(color("\n== storage ==", "b"))
    print("\n".join("  " + l for l in kube(["get", "pvc", "-A"]).stdout.rstrip().splitlines()))
    return 0


def cmd_diff(a):
    """Server-side dry-run diff of rendered output vs live. Read-only."""
    need_cluster()
    apps = load_apps(a.deprecated)
    targets = apps if a.all else [resolve(a.app, apps)]
    os.makedirs(OUT, exist_ok=True)
    drift = 0
    for name, spec, rel, meta in targets:
        ok, text, warns = render_app(name, spec, rel, meta)
        if not ok:
            print(f"{color('FAIL', 'r')} {name}: {text.splitlines()[0] if text else ''}")
            continue
        if not text.strip():
            print(f"{color(' EMPTY', 'y')} {name} (renders nothing)")
            continue
        dest = os.path.join(OUT, f"{name}.yaml")
        open(dest, "w").write(text)
        p = kube(["diff", "-f", dest], timeout=180)
        # kubectl diff: 0 = no drift, 1 = drift, >1 = error
        if p.returncode == 0:
            print(f"{color('  same  ', 'g')} {name}")
        elif p.returncode == 1:
            drift += 1
            n = len([l for l in p.stdout.splitlines() if l.startswith(("+", "-"))])
            print(f"{color('  DRIFT ', 'y')} {name}  ({n} changed lines)")
            if not a.quiet:
                print("\n".join("    " + l for l in p.stdout.splitlines()[:a.context]))
        else:
            print(f"{color('  ERROR ', 'r')} {name}: {p.stderr.strip().splitlines()[0]}")
    print(f"\n{drift} app(s) differ from live")
    return 0


def cmd_ingress(a):
    """Hit every ingress host through Traefik and check TLS + response."""
    need_cluster()
    p = kube(["get", "ingress", "-A", "-o", "json"])
    hosts = []
    for it in json.loads(p.stdout)["items"]:
        for r in it["spec"].get("rules", []):
            if r.get("host"):
                hosts.append((it["metadata"]["namespace"], r["host"]))
    ip = a.node_ip
    for ns, h in sorted(set(hosts)):
        # resolve through the node directly; DNS is public but the node is LAN-only
        cmd = ["curl", "-sS", "-o", "/dev/null", "--max-time", "20",
               "--resolve", f"{h}:443:{ip}",
               "-w", "%{http_code} tls=%{ssl_verify_result} time=%{time_total}s",
               f"https://{h}/"]
        r = run(cmd, timeout=30)
        out = r.stdout.strip() or r.stderr.strip().splitlines()[-1]
        code = out.split()[0] if r.returncode == 0 else "ERR"
        ok = r.returncode == 0 and code[:1] in ("2", "3", "4")
        print(f"  {color('ok  ' if ok else 'FAIL', 'g' if ok else 'r')} "
              f"{h:36} {ns:16} {out}")
    return 0


def cmd_logs(a):
    need_cluster()
    p = kube(["get", "pods", "-A", "-o", "json"])
    hits = [(i["metadata"]["namespace"], i["metadata"]["name"])
            for i in json.loads(p.stdout)["items"] if a.app in i["metadata"]["name"]]
    if not hits:
        sys.exit(f"no pod name contains {a.app!r}")
    for ns, pod in hits[:a.limit]:
        print(color(f"== {ns}/{pod} ==", "b"))
        print(kube(["logs", "-n", ns, pod, f"--tail={a.tail}", "--all-containers"],
                   timeout=60).stdout.rstrip())
    return 0


def cmd_waves(a):
    """Sync-wave ordering -- the order ArgoCD actually applies things."""
    apps = load_apps(a.deprecated)
    buckets = {}
    for name, spec, rel, meta in apps:
        buckets.setdefault(wave(meta), []).append((name, rel))
    for w in sorted(buckets, key=lambda x: (x == "-", x)):
        print(color(f"wave {w}", "b"))
        for name, rel in sorted(buckets[w]):
            print(f"  {name:34} {color(rel, 'd')}")
    return 0


def cmd_ansible(a):
    """Syntax-check the playbooks. No host is contacted."""
    d = os.path.join(REPO, "system", "ansible")
    # ~/.local/bin/ansible-playbook has a #!/usr/bin/python3 shebang and that
    # interpreter has no ansible module -- the working one is in the venv.
    ap_bin = next((c for c in (os.path.expanduser("~/.venv/ansible/bin/ansible-playbook"),
                               shutil.which("ansible-playbook"))
                   if c and os.path.exists(c)), None)
    if not ap_bin:
        sys.exit("no working ansible-playbook found")
    inv = f"inventories/{a.env}/inventory.yml"
    rc = 0
    for pb in sorted(glob.glob(os.path.join(d, "playbooks", "*.yml"))):
        rel = os.path.relpath(pb, d)
        p = run([ap_bin, "-i", inv, "--syntax-check", rel],
                cwd=d, timeout=120)
        ok = p.returncode == 0
        rc |= p.returncode
        print(f"  {color('ok  ' if ok else 'FAIL', 'g' if ok else 'r')} {rel}")
        if not ok:
            print("\n".join("      " + l for l in p.stderr.strip().splitlines()[:6]))
    return 1 if rc else 0


def cmd_smoke(a):
    """Everything that is safe to run unattended."""
    rc = 0
    print(color("### waves ###", "b"));   rc |= cmd_waves(a)
    print(color("\n### lint ###", "b"));  rc |= cmd_lint(a)
    if not a.offline:
        print(color("\n### status ###", "b"));  rc |= cmd_status(a)
        print(color("\n### ingress ###", "b")); rc |= cmd_ingress(a)
    return rc


def main():
    ap = argparse.ArgumentParser(prog="driver.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deprecated", action="store_true",
                    help="include app/deprecated/ (excluded by the bootstrap app)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("render", help="reproduce what ArgoCD renders (offline)")
    s.add_argument("app", nargs="?")
    s.add_argument("--all", action="store_true")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("lint", help="render everything + validate objects (offline)")
    s.add_argument("--cluster", action="store_true",
                   help="validate against live API schemas instead of offline")
    s.set_defaults(fn=cmd_lint)

    s = sub.add_parser("status", help="read-only live cluster overview")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("diff", help="server-side dry-run diff vs live (read-only)")
    s.add_argument("app", nargs="?")
    s.add_argument("--all", action="store_true")
    s.add_argument("--quiet", action="store_true", help="counts only, no hunks")
    s.add_argument("--context", type=int, default=40, help="max diff lines per app")
    s.set_defaults(fn=cmd_diff)

    s = sub.add_parser("ingress", help="curl every ingress host through Traefik")
    s.add_argument("--node-ip", default="192.168.1.100")
    s.set_defaults(fn=cmd_ingress)

    s = sub.add_parser("logs", help="tail logs of pods matching a name")
    s.add_argument("app")
    s.add_argument("--tail", type=int, default=40)
    s.add_argument("--limit", type=int, default=3)
    s.set_defaults(fn=cmd_logs)

    s = sub.add_parser("waves", help="sync-wave ordering from git")
    s.set_defaults(fn=cmd_waves)

    s = sub.add_parser("ansible", help="syntax-check playbooks")
    s.add_argument("--env", default="prod", choices=["dev", "prod"])
    s.set_defaults(fn=cmd_ansible)

    s = sub.add_parser("smoke", help="waves + lint + status + ingress")
    s.add_argument("--offline", action="store_true", help="skip cluster checks")
    s.add_argument("--cluster", action="store_true")
    s.add_argument("--node-ip", default="192.168.1.100")
    s.set_defaults(fn=cmd_smoke)

    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
