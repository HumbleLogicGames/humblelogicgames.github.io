#!/usr/bin/env python3
"""Publish the intro pages built by build.py to S3 + CloudFront.

DRY RUN BY DEFAULT: prints every AWS command and changes nothing.
Add --go only after Yongwoo approved the publish (card / 팀장).

  python3 tools/subsites/publish.py                 # dry run, all hosts
  python3 tools/subsites/publish.py sudoku onet     # dry run, some hosts
  python3 tools/subsites/publish.py --setup         # dry run of the one-time shared distribution setup
  python3 tools/subsites/publish.py --go sudoku     # real upload (after approval)

Where pages go:
  * Existing per-game distributions (sudoku, mahjong, solitaire, spider): bucket root.
    The old web game in that bucket is first copied to ~/Projects/hlg-web-backup/<host>-<date>/,
    then removed by `sync --delete` (d290: other games' web builds stay unpublished).
  * New games (tilematch, onet, bubblepop, nutsxbolts, wordsolitaire, amazeout, decodit):
    one shared bucket + one CloudFront distribution, folder per host, routed by router.js.
  * dominoes: NOT handled here. domino's publish_web.sh owns that bucket (game at /play.html).
"""
import datetime
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITES = ROOT / "_subsites"
HERE = Path(__file__).resolve().parent
ACCOUNT = "367836725145"
REGION = "ap-northeast-2"
DOMAIN = "humblelogicgames.com"
CERT = f"arn:aws:acm:us-east-1:{ACCOUNT}:certificate/f1b7e6f1-3372-46c3-bd72-d61e2774aedd"
OAC = "E5YM8B82T55F6"  # existing Origin Access Control used by every web distribution

EXISTING = {  # host -> (bucket, distribution id)
    "sudoku": (f"sudoku-web-{ACCOUNT}", "E16SPKJZ4ADGVX"),
    "mahjong": (f"mahjong-web-{ACCOUNT}", "E1ALF6TALPDIXQ"),
    "solitaire": (f"solitaire-web-{ACCOUNT}", "E1SWA1JRXDQF4B"),
    "spider": (f"spider-web-{ACCOUNT}", "EQ6YP7SAQAAPS"),
}
SHARED_BUCKET = f"hlg-sites-{ACCOUNT}"
SHARED_HOSTS = ["tilematch", "onet", "bubblepop", "nutsxbolts", "wordsolitaire", "amazeout", "decodit"]
SHARED_DIST_FILE = HERE / "shared_distribution.txt"  # written by --setup --go: the new distribution id
FUNCTION = "hlg-sites-router"

GO = "--go" in sys.argv


def run(cmd, capture=False):
    print("  $", " ".join(shlex.quote(c) for c in cmd))
    if not GO:
        return ""
    r = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return r.stdout if capture else ""


def upload(src, dest):
    # pages: always revalidate; assets: cache one day
    run(["aws", "s3", "sync", str(src), dest, "--delete", "--exclude", "*", "--include", "*.html",
         "--cache-control", "no-cache", "--content-type", "text/html; charset=utf-8"])
    run(["aws", "s3", "sync", str(src), dest, "--delete", "--exclude", "*.html",
         "--cache-control", "public, max-age=86400"])


def shared_dist():
    if SHARED_DIST_FILE.exists():
        return SHARED_DIST_FILE.read_text().strip()
    return "<SHARED_DIST_ID: run --setup first>"


def setup():
    """One-time: shared bucket, router function, shared distribution."""
    print(f"\n# setup: bucket {SHARED_BUCKET}, function {FUNCTION}, one distribution for {len(SHARED_HOSTS)} hosts")
    run(["aws", "s3api", "create-bucket", "--bucket", SHARED_BUCKET, "--region", REGION,
         "--create-bucket-configuration", f"LocationConstraint={REGION}"])
    run(["aws", "s3api", "put-public-access-block", "--bucket", SHARED_BUCKET, "--public-access-block-configuration",
         "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"])
    fn_cfg = json.dumps({"Comment": "intro pages: host -> folder", "Runtime": "cloudfront-js-2.0"})
    out = run(["aws", "cloudfront", "create-function", "--name", FUNCTION, "--function-config", fn_cfg,
               "--function-code", f"fileb://{HERE / 'router.js'}"], capture=True)
    etag = json.loads(out)["ETag"] if out else "<ETAG>"
    run(["aws", "cloudfront", "publish-function", "--name", FUNCTION, "--if-match", etag])
    fn_arn = f"arn:aws:cloudfront::{ACCOUNT}:function/{FUNCTION}"
    aliases = [f"{h}.{DOMAIN}" for h in SHARED_HOSTS]
    cfg = {
        "CallerReference": f"hlg-sites-{datetime.date.today()}",
        "Comment": "HLG game intro pages (shared)",
        "Enabled": True,
        "Aliases": {"Quantity": len(aliases), "Items": aliases},
        "DefaultRootObject": "",
        "Origins": {"Quantity": 1, "Items": [{
            "Id": "s3", "DomainName": f"{SHARED_BUCKET}.s3.{REGION}.amazonaws.com",
            "OriginAccessControlId": OAC, "S3OriginConfig": {"OriginAccessIdentity": ""}}]},
        "DefaultCacheBehavior": {
            "TargetOriginId": "s3", "ViewerProtocolPolicy": "redirect-to-https", "Compress": True,
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # AWS managed CachingOptimized
            "FunctionAssociations": {"Quantity": 1, "Items": [{"EventType": "viewer-request", "FunctionARN": fn_arn}]}},
        "ViewerCertificate": {"ACMCertificateArn": CERT, "SSLSupportMethod": "sni-only",
                              "MinimumProtocolVersion": "TLSv1.2_2021"},
        "PriceClass": "PriceClass_All",
        "HttpVersion": "http2and3",
    }
    out = run(["aws", "cloudfront", "create-distribution", "--distribution-config", json.dumps(cfg)], capture=True)
    dist_id = json.loads(out)["Distribution"]["Id"] if out else "<NEW_DIST_ID>"
    if GO:
        SHARED_DIST_FILE.write_text(dist_id + "\n")
    policy = {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow", "Principal": {"Service": "cloudfront.amazonaws.com"}, "Action": "s3:GetObject",
        "Resource": f"arn:aws:s3:::{SHARED_BUCKET}/*",
        "Condition": {"StringEquals": {"AWS:SourceArn": f"arn:aws:cloudfront::{ACCOUNT}:distribution/{dist_id}"}}}]}
    run(["aws", "s3api", "put-bucket-policy", "--bucket", SHARED_BUCKET, "--policy", json.dumps(policy)])
    print("  # then: DNS CNAME for each host -> the new distribution's xxxx.cloudfront.net (Yongwoo, Squarespace)")


def publish(hosts):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    touched_shared = False
    for h in hosts:
        src = SITES / h
        if not (src / "index.html").exists():
            sys.exit(f"{h}: {src}/index.html missing — run build.py first")
        if h in EXISTING:
            bucket, dist = EXISTING[h]
            print(f"\n# {h}: bucket root = intro page (an old web game there is backed up first)")
            has_game = not GO or "index.pck" in subprocess.run(["aws", "s3", "ls", f"s3://{bucket}/index.pck"],
                                                                text=True, capture_output=True).stdout
            if has_game:
                run(["aws", "s3", "sync", f"s3://{bucket}/", str(Path.home() / "Projects/hlg-web-backup" / f"{h}-{stamp}")])
            upload(src, f"s3://{bucket}/")
            run(["aws", "cloudfront", "create-invalidation", "--distribution-id", dist, "--paths", "/*"])
        elif h in SHARED_HOSTS:
            print(f"\n# {h}: shared bucket folder")
            upload(src, f"s3://{SHARED_BUCKET}/{h}/")
            touched_shared = True
        elif h == "dominoes":
            print("\n# dominoes: skipped — domino's publish_web.sh publishes it (intro at /, game at /play.html)")
        else:
            sys.exit(f"{h}: unknown host")
    if touched_shared:
        run(["aws", "cloudfront", "create-invalidation", "--distribution-id", shared_dist(), "--paths", "/*"])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print("MODE:", "REAL (--go)" if GO else "dry run — nothing is changed")
    if "--setup" in sys.argv:
        setup()
    else:
        publish(args or [*EXISTING, *SHARED_HOSTS, "dominoes"])
