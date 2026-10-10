# -*- coding: utf-8 -*-
"""Whitelist-targeted EuropePMC retrieval (2026-10-09 回顾模式专用，一次性批跑脚本).

在 gdd_search.py / gdd_search_extra.py 的 6 组主题词基础上，叠加 JOURNAL 定向子句
（严格 T1/T2 白名单 20 本刊的全称/简称变体），实现"白名单宇宙内的全量检索"——
用户 2026-10-09 约定：白名单之外的文献不需要检索。
写入 raw/epmc_raw.json（topic 键与 6 组主题同名，供 gdd_build_db.py --merge 合并）。

Usage:
  python gdd_search_targeted.py --dir WORKDIR --from 2024-01-01 --to 2024-12-31 [--max-pages 30]
"""
import argparse, json, os, ssl, time, urllib.parse, urllib.request

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research-literature-agent)"}

CORE = (
    '(TITLE_ABS:"drug delivery" OR TITLE_ABS:"drug delivery system*" '
    'OR TITLE_ABS:DDS OR TITLE_ABS:"drug carrier*" OR TITLE_ABS:"delivery vehicle*" '
    'OR TITLE_ABS:nanocarrier* OR TITLE_ABS:nanomedicine* OR TITLE_ABS:nanomedicinal '
    'OR TITLE_ABS:nanoformulation* OR TITLE_ABS:"pharmaceutical formulation*")'
)
CARRIER = (
    '(TITLE_ABS:nanocarrier* OR TITLE_ABS:nanoparticle* OR TITLE_ABS:liposome* '
    'OR TITLE_ABS:"lipid nanoparticle*" OR TITLE_ABS:"polymeric nanoparticle*" '
    'OR TITLE_ABS:micelle* OR TITLE_ABS:dendrimer* OR TITLE_ABS:hydrogel* '
    'OR TITLE_ABS:microsphere* OR TITLE_ABS:nanocrystal* OR TITLE_ABS:exosome* '
    'OR TITLE_ABS:"extracellular vesicle*")'
)
GUT = (
    '(TITLE_ABS:gut OR TITLE_ABS:gastrointestin* OR TITLE_ABS:intestin* '
    'OR TITLE_ABS:colon OR TITLE_ABS:colonic OR TITLE_ABS:colorectal '
    'OR TITLE_ABS:"colon-specific" OR TITLE_ABS:"colon-target*" OR TITLE_ABS:"gut-target*" '
    'OR TITLE_ABS:bowel OR TITLE_ABS:ileum OR TITLE_ABS:ileal OR TITLE_ABS:jejunum '
    'OR TITLE_ABS:jejunal OR TITLE_ABS:duodenum OR TITLE_ABS:duodenal '
    'OR TITLE_ABS:cecum OR TITLE_ABS:caecum OR TITLE_ABS:rectum OR TITLE_ABS:enteral '
    'OR TITLE_ABS:"gastrointestinal tract" OR TITLE_ABS:"GI tract")'
)
APP = (
    '(TITLE_ABS:therapeut* OR TITLE_ABS:treatment* OR TITLE_ABS:biomedic* '
    'OR TITLE_ABS:disease* OR TITLE_ABS:bioavailabilit* OR TITLE_ABS:absorption '
    'OR TITLE_ABS:microbiome OR TITLE_ABS:"gut microbiota" '
    'OR TITLE_ABS:"inflammatory bowel" OR TITLE_ABS:IBD OR TITLE_ABS:Crohn '
    'OR TITLE_ABS:"ulcerative colitis" OR TITLE_ABS:pharmacokinet* OR TITLE_ABS:diagnos*)'
)
CARRIER_DETAIL = (
    '(TITLE_ABS:liposome* OR TITLE_ABS:"lipid nanoparticle*" '
    'OR TITLE_ABS:"solid lipid nanoparticle*" OR TITLE_ABS:PLGA OR TITLE_ABS:chitosan '
    'OR TITLE_ABS:dendrimer* OR TITLE_ABS:polymersome* OR TITLE_ABS:niosome* '
    'OR TITLE_ABS:"metal-organic framework*" OR TITLE_ABS:MOF '
    'OR TITLE_ABS:"mesoporous silica*" OR TITLE_ABS:"cell membrane-coated" '
    'OR TITLE_ABS:exosome* OR TITLE_ABS:"extracellular vesicle*" '
    'OR TITLE_ABS:"albumin nanoparticle*" OR TITLE_ABS:nanocrystal* '
    'OR TITLE_ABS:hydrogel* OR TITLE_ABS:microsphere* OR TITLE_ABS:emulsion*)'
)
GUT_STRATEGY = (
    '(TITLE_ABS:"oral delivery" OR TITLE_ABS:"oral drug delivery" OR TITLE_ABS:enteric '
    'OR TITLE_ABS:"colon-specific" OR TITLE_ABS:"colon-targeted" OR TITLE_ABS:"site-specific" '
    'OR TITLE_ABS:"mucus penetration" OR TITLE_ABS:"mucus-penetrating" OR TITLE_ABS:mucus '
    'OR TITLE_ABS:"Peyer\'s patch*" OR TITLE_ABS:"intestinal absorption" '
    'OR TITLE_ABS:"intestinal permeab*" OR TITLE_ABS:"gut microbiota" OR TITLE_ABS:microbiome '
    'OR TITLE_ABS:bioavailabilit*)'
)
DD_LITE = (
    '(TITLE_ABS:"drug deliver*" OR TITLE_ABS:nanocarrier* OR TITLE_ABS:"drug carrier*" '
    'OR TITLE_ABS:formulation* OR TITLE_ABS:liposome* OR TITLE_ABS:nanoparticle*)'
)
STRATEGY = (
    '(TITLE_ABS:targeting OR TITLE_ABS:"controlled release" OR TITLE_ABS:"sustained release" '
    'OR TITLE_ABS:"stimuli-responsive" OR TITLE_ABS:"pH-responsive" '
    'OR TITLE_ABS:"responsive release" OR TITLE_ABS:"gene delivery" '
    'OR TITLE_ABS:siRNA OR TITLE_ABS:mRNA OR TITLE_ABS:CRISPR '
    'OR TITLE_ABS:theranostic* OR TITLE_ABS:PEGylation OR TITLE_ABS:"oral delivery")'
)

# ---- T1/T2 白名单 20 本刊：JOURNAL 定向子句（全称 + NLM 简写变体）----
JL = (
    '(JOURNAL:"Nature" OR JOURNAL:"Science" OR JOURNAL:"Nature reviews drug discovery" '
    'OR JOURNAL:"Nat rev drug discov" OR JOURNAL:"Chemical reviews" OR JOURNAL:"Chem rev" '
    'OR JOURNAL:"Chemical society reviews" OR JOURNAL:"Chem soc rev" '
    'OR JOURNAL:"Nature nanotechnology" OR JOURNAL:"Nat nanotechnol" '
    'OR JOURNAL:"Nature materials" OR JOURNAL:"Nat mater" '
    'OR JOURNAL:"Nature biomedical engineering" OR JOURNAL:"Nat biomed eng" '
    'OR JOURNAL:"Advanced materials" OR JOURNAL:"Adv mater" '
    'OR JOURNAL:"Angewandte chemie" OR JOURNAL:"Angew chem" '
    'OR JOURNAL:"Journal of controlled release" OR JOURNAL:"J control release" '
    'OR JOURNAL:"Advanced drug delivery reviews" OR JOURNAL:"Adv drug deliv rev" '
    'OR JOURNAL:"ACS nano" OR JOURNAL:"Nano today" OR JOURNAL:"Biomaterials" '
    'OR JOURNAL:"Matter" OR JOURNAL:"Nature communications" OR JOURNAL:"Nat commun" '
    'OR JOURNAL:"Science advances" OR JOURNAL:"Sci adv" '
    'OR JOURNAL:"Nano letters" OR JOURNAL:"Nano lett" OR JOURNAL:"JACS" '
    'OR JOURNAL:"Journal of the American chemical society" OR JOURNAL:"J am chem soc")'
)


def queries(date):
    return {
        "DD-CORE": f'{CORE} AND {CARRIER} AND ({JL}) AND (FIRST_PDATE:[{date}])',
        "GUT-DD": f'{CORE} AND {GUT} AND ({JL}) AND (FIRST_PDATE:[{date}])',
        "GUT-BIO": f'{CARRIER} AND {GUT} AND {APP} AND ({JL}) AND (FIRST_PDATE:[{date}])',
        "DD-CARRIER": f'{CORE} AND {CARRIER_DETAIL} AND ({JL}) AND (FIRST_PDATE:[{date}])',
        "GUT-ORAL": f'{GUT} AND {GUT_STRATEGY} AND {DD_LITE} AND ({JL}) AND (FIRST_PDATE:[{date}])',
        "DD-STRATEGY": f'{CORE} AND {STRATEGY} AND ({JL}) AND (FIRST_PDATE:[{date}])',
    }


def fetch(url, tries=6, wait=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("  retry", i + 1, str(e)[:70])
            time.sleep(wait * (i // 2 + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.getcwd())
    ap.add_argument("--from", dest="dfrom", required=True)
    ap.add_argument("--to", dest="dto", required=True)
    ap.add_argument("--max-pages", type=int, default=30)
    args = ap.parse_args()

    date = f"{args.dfrom} TO {args.dto}"
    raw_path = os.path.join(args.dir, "raw", "epmc_raw.json")
    raw = {}
    for name, q in queries(date).items():
        print(f"=== EPMC-TARGETED {name} ===")
        cursor, items = "*", []
        for page in range(args.max_pages):
            params = {"query": q, "format": "json", "pageSize": "100",
                      "resultType": "core", "cursorMark": cursor}
            data = fetch(EPMC + "?" + urllib.parse.urlencode(params))
            if not data:
                print("  page", page, "FAILED"); break
            res = data.get("resultList", {}).get("result", [])
            items.extend(res)
            print(f"  page {page}: {len(res)} hits (total {data.get('hitCount')})")
            nxt = data.get("nextCursorMark")
            if not nxt or nxt == cursor or not res:
                break
            cursor = nxt
            time.sleep(1.2)
        raw[name] = items
        print(f"{name}: {len(items)} records")
        time.sleep(1.2)

    json.dump(raw, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved to", raw_path, "| topics:", {k: len(v) for k, v in raw.items()})


if __name__ == "__main__":
    main()
