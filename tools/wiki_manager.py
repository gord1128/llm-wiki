#!/usr/bin/env python3
import os
import sys
import glob
import re
import subprocess
import datetime
import urllib.request
import json
import argparse

# Ensure tools directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from fts_engine import FTSIndex

WIKI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Optional Discord notification integration via Webhook URL or Bot Token
# Configure via environment variables:
#   WIKI_DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
#   or WIKI_DISCORD_BOT_TOKEN="your_token" and WIKI_DISCORD_CHANNEL_ID="channel_id"
DISCORD_WEBHOOK_URL = os.environ.get("WIKI_DISCORD_WEBHOOK_URL")
DISCORD_CHANNEL = os.environ.get("WIKI_DISCORD_CHANNEL_ID")
DISCORD_TOKEN = os.environ.get("WIKI_DISCORD_BOT_TOKEN") or os.environ.get("DISCORD_BOT_TOKEN")

def send_discord_notification(title, summary, category, path):
    embed = {
        "title": f"📚 [Wiki 업데이트] {title}",
        "description": summary,
        "color": 3447003, # Deep Blue
        "fields": [
            {"name": "분류", "value": category, "inline": True},
            {"name": "경로", "value": f"`{path}`", "inline": True}
        ],
        "footer": {"text": "Obsidian LLM Wiki • Autonomous Knowledge Engine"}
    }
    
    payload_bytes = json.dumps({"embeds": [embed]}).encode("utf-8")
    
    # 1. Webhook URL 우선 지원
    if DISCORD_WEBHOOK_URL:
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Hermes-WikiManager/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status in [200, 204]:
                    print("[WikiManager] Discord webhook notification sent successfully.")
                    return
        except Exception as e:
            print(f"[WikiManager] Discord webhook notification failed: {e}")
            return

    # 2. Bot Token + Channel ID 지원
    if DISCORD_TOKEN and DISCORD_CHANNEL:
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL}/messages",
            data=payload_bytes,
            headers={
                "Authorization": f"Bot {DISCORD_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "Hermes-WikiManager/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status in [200, 201]:
                    print("[WikiManager] Discord notification sent successfully.")
                else:
                    print(f"[WikiManager] Discord notification response status: {res.status}")
        except Exception as e:
            print(f"[WikiManager] Error sending Discord notification: {e}")
    else:
        # 알림 미설정 시 경고 없이 안전 통과
        pass

def git_commit(message):
    try:
        subprocess.run(["git", "add", "."], cwd=WIKI_ROOT, check=True)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=WIKI_ROOT, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "commit", "-m", message], cwd=WIKI_ROOT, check=True)
            print(f"[WikiManager] Git committed: {message}")
        else:
            print("[WikiManager] No git changes to commit.")
    except Exception as e:
        print(f"[WikiManager] Git commit failed: {e}")

def log_change(title, action, doc_name):
    today = datetime.date.today().strftime("%Y-%m-%d")
    log_path = os.path.join(WIKI_ROOT, "log.md")
    new_entry = f"- **{action}**: [[{doc_name}]] - {title}\n"
    
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        header = f"## {today}\n"
        if header in lines:
            idx = lines.index(header) + 1
            lines.insert(idx, new_entry)
        else:
            if len(lines) > 0 and lines[0].startswith("# "):
                lines.insert(2, f"\n{header}{new_entry}")
            else:
                lines.insert(0, f"{header}{new_entry}")
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    else:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"# Knowledge Base Changelog\n\n## {today}\n{new_entry}")

def parse_simple_yaml(text):
    data = {}
    current_key = None
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_key:
            val = line[2:].strip().strip("\"'")
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(val)
        elif ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                items = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
                data[k] = items
                current_key = None
            elif not v:
                data[k] = []
                current_key = k
            else:
                data[k] = v.strip("\"'")
                current_key = None
    return data

def extract_lod1(body):
    # LOD 1 (TL;DR / 핵심 요약): '## 요약 (TL;DR)' 또는 '## 개요' 섹션 추출
    m = re.search(r"##\s*(?:요약(?:\s*\(TL;DR\))?|개요)\s*\n+([^#]+)", body, re.IGNORECASE)
    if m:
        summary_raw = m.group(1).strip()
        lines = [l.strip() for l in summary_raw.split("\n") if l.strip()]
        return "\n".join(lines[:6])
    lines = [l.strip() for l in body.strip().split("\n") if l.strip() and not l.startswith("#")]
    return lines[0] if lines else ""

def get_all_wiki_docs():
    wiki_files = glob.glob(os.path.join(WIKI_ROOT, "wiki", "**", "*.md"), recursive=True)
    docs = []
    for f in wiki_files:
        stem = os.path.splitext(os.path.basename(f))[0]
        # 카테고리 index.md 파일은 일반 문서 컬렉션에서 제외
        if stem == "index":
            continue
            
        rel_path = os.path.relpath(f, WIKI_ROOT)
        with open(f, "r", encoding="utf-8") as doc:
            content = doc.read()
        fm = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parse_simple_yaml(parts[1])
                body = parts[2]
        
        lod1 = extract_lod1(body)
        summary = lod1.split("\n")[0] if lod1 else fm.get("title", stem)
        links = [l.strip().split("#")[0] for l in re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)]
        
        docs.append({
            "stem": stem,
            "path": f,
            "rel_path": rel_path,
            "title": fm.get("title", stem),
            "type": fm.get("type", "concept"),
            "tags": fm.get("tags", []),
            "sources": fm.get("sources", []),
            "updated": fm.get("updated", ""),
            "related": fm.get("related", []),
            "summary": summary,
            "lod1": lod1,
            "links": links,
            "body": body,
            "raw_content": content
        })
    return docs

def reindex_wiki():
    print("[WikiManager] 색인(index.md), 서브 MOC 및 FTS5 엔진 증분 동기화 중...")
    docs = get_all_wiki_docs()
    
    # 1. FTS5 전문 검색 엔진 인덱스 갱신
    fts = FTSIndex()
    updated_fts = fts.sync_all(docs)
    fts.close()
    print(f"[WikiManager] FTS5 검색 엔진 동기화 완료 ({updated_fts}개 문서 인덱스 갱신됨).")
    
    cats = {
        "concept": {"title": "Concepts", "korean": "개념 및 구조", "dir": "wiki/concepts", "items": []},
        "tool": {"title": "Tools", "korean": "도구 및 환경", "dir": "wiki/tools", "items": []},
        "troubleshooting": {"title": "Troubleshooting", "korean": "트러블슈팅 및 해결책", "dir": "wiki/troubleshooting", "items": []}
    }
    
    for d in sorted(docs, key=lambda x: x["title"]):
        t = d["type"]
        if t in cats:
            cats[t]["items"].append(d)
        else:
            cats["concept"]["items"].append(d)
            
    # 2. 서브 MOC (wiki/<cat>/index.md) 생성
    for c_key, c_data in cats.items():
        c_dir = os.path.join(WIKI_ROOT, c_data["dir"])
        os.makedirs(c_dir, exist_ok=True)
        sub_moc_lines = [
            f"# {c_data['title']} (MOC)",
            f"\n{c_data['korean']} 관련 위키 지식 지도입니다.\n",
            "## 수록 문서 목록"
        ]
        for item in c_data["items"]:
            tags_disp = " ".join([f"`#{t}`" for t in item["tags"][:3]])
            sub_moc_lines.append(f"- [[{item['stem']}]]: **{item['title']}** {tags_disp}\n  > {item['summary']}")
            
        sub_moc_content = "\n".join(sub_moc_lines) + "\n"
        with open(os.path.join(c_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(sub_moc_content)

    # 3. 루트 index.md (경량 Map of Contents - 300토큰 이내)
    recent_docs = sorted(docs, key=lambda x: x.get("updated", ""), reverse=True)[:5]
    root_lines = [
        "# LLM Knowledge Base Index (MOC)\n",
        "개인 지식 베이스의 최상위 목차(Map of Contents)입니다. 상세 분야는 하위 MOC를 탐색합니다.\n",
        "## 🧭 주요 지식 클러스터 (MOC)"
    ]
    for c_key, c_data in cats.items():
        root_lines.append(f"- **[[{c_data['dir']}/index|{c_data['title']} ({c_data['korean']})]]** — 총 {len(c_data['items'])}개 문서")
        
    root_lines.append("\n## 🕒 최근 갱신된 지식 (Recent Updates)")
    for rd in recent_docs:
        root_lines.append(f"- [[{rd['stem']}]]: {rd['title']} (`{rd.get('updated', 'N/A')}`)")
        
    root_lines.append("\n## ⚡ 고속 검색 안내")
    root_lines.append("- CLI 질의: `python3 tools/wiki_manager.py query \"<검색어>\" --lod 1` (LOD 1 요약 모드)")
    
    with open(os.path.join(WIKI_ROOT, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(root_lines) + "\n")
    print(f"[WikiManager] 루트 index.md 및 3개 서브 MOC 갱신 완료.")

    # 4. _sidebar.md 생성 (Docsify 호환)
    sb_lines = [
        "- **[홈으로 (Index)](index.md)**\n",
        "- **Concepts**"
    ]
    for item in cats["concept"]["items"]:
        sb_lines.append(f"  - [{item['title']}](wiki/concepts/{item['stem']}.md)")
        
    sb_lines.append("- **Tools**")
    for item in cats["tool"]["items"]:
        sb_lines.append(f"  - [{item['title']}](wiki/tools/{item['stem']}.md)")
        
    sb_lines.append("- **Troubleshooting**")
    for item in cats["troubleshooting"]["items"]:
        sb_lines.append(f"  - [{item['title']}](wiki/troubleshooting/{item['stem']}.md)")
        
    sb_lines.append("\n- **[변경 기록 (Changelog)](log.md)**")
    sb_lines.append("- **[위키 스키마 (SCHEMA)](SCHEMA.md)**\n")
    
    with open(os.path.join(WIKI_ROOT, "_sidebar.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(sb_lines))
    print("[WikiManager] _sidebar.md 갱신 완료.")

def run_linter():
    print("=== [Wiki Linter] 정합성 및 무결성 검증 시작 ===")
    errors = []
    warnings = []
    
    docs = get_all_wiki_docs()
    wiki_stem_map = {d["stem"]: d["path"] for d in docs}
    print(f"[*] 총 {len(docs)}개의 위키 문서 발견.")
    
    required_keys = ["title", "type", "tags", "sources", "updated"]
    valid_types = ["concept", "tool", "troubleshooting"]
    
    for d in docs:
        rel_path = d["rel_path"]
        stem = d["stem"]
        
        for req in required_keys:
            if not d.get(req):
                errors.append(f"[{rel_path}] 필수 Frontmatter 필드 누락: '{req}'")
                
        if d.get("type") and d["type"] not in valid_types:
            warnings.append(f"[{rel_path}] 정의되지 않은 type '{d['type']}' (허용: {valid_types})")
            
        for src in d.get("sources", []):
            src_full = os.path.join(WIKI_ROOT, src)
            if not os.path.isfile(src_full):
                errors.append(f"[{rel_path}] 출처 파일 부재: {src}")
            elif os.path.getsize(src_full) == 0:
                warnings.append(f"[{rel_path}] 출처 파일 비어있음: {src}")

        for target in d.get("links", []):
            if not target:
                continue
            # 서브 MOC 링크 허용
            if "index" in target:
                continue
            if target not in wiki_stem_map:
                errors.append(f"[{rel_path}] 깨진 위키링크 발견: [[{target}]] -> 해당 문서 없음")

    print("-" * 50)
    if warnings:
        print(f"[!] 경고 ({len(warnings)}건):")
        for w in warnings:
            print(f"  - {w}")
    
    if errors:
        print(f"[X] 오류 ({len(errors)}건) 발생:")
        for e in errors:
            print(f"  - {e}")
        print("=== [Wiki Linter] 검증 실패 (오류를 해결하세요) ===")
        return 1
    else:
        print(f"[V] 모든 검증 통과 완료! (문서: {len(docs)}개, 에러: 0개)")
        print("=== [Wiki Linter] 검증 성공 ===")
        return 0

def audit_wiki():
    print("=== [Wiki Knowledge Graph Audit & Compaction Report] ===")
    docs = get_all_wiki_docs()
    total_docs = len(docs)
    
    inbound_count = {d["stem"]: 0 for d in docs}
    for d in docs:
        for l in d["links"]:
            if l in inbound_count:
                inbound_count[l] += 1
                
    tag_counter = {}
    tag_doc_map = {}
    for d in docs:
        for t in d["tags"]:
            tag_counter[t] = tag_counter.get(t, 0) + 1
            if t not in tag_doc_map:
                tag_doc_map[t] = []
            tag_doc_map[t].append(d["stem"])
            
    print(f"[*] 총 수록 문서: {total_docs}개")
    print(f"[*] 활용 중인 고유 태그: {len(tag_counter)}개")
    
    islands = []
    for d in docs:
        out_cnt = len(d["links"])
        in_cnt = inbound_count[d["stem"]]
        if out_cnt <= 1 and in_cnt <= 1:
            islands.append((d["title"], d["stem"], out_cnt, in_cnt))
            
    print("\n[📊 지식 그래프 연결도 분석]")
    for d in docs:
        out_cnt = len(d["links"])
        in_cnt = inbound_count[d["stem"]]
        print(f"  - [[{d['stem']}]] ({d['title']}): 나가는 링크 {out_cnt}개, 들어오는 링크 {in_cnt}개")
        
    print("\n[🔍 지식 확장 추천 대상 (연결도 낮은 문서)]")
    if islands:
        for title, stem, out_c, in_c in islands:
            print(f"  * [[{stem}]] ({title}) -> 연관 문서 추가 링크 또는 상위 개념 보강 권장")
    else:
        print("  * 모든 문서가 충분한 상호 연결을 유지하고 있습니다.")

    print("\n[📦 지식 압축 진단 (Knowledge Compaction Alerts)]")
    compaction_candidates = []
    for t, count in tag_counter.items():
        if count >= 3:
            compaction_candidates.append((t, count, tag_doc_map[t]))
            
    if compaction_candidates:
        for t, count, stems in compaction_candidates:
            stems_str = ", ".join([f"[[{s}]]" for s in stems])
            print(f"  ⚠️  태그 '#{t}'에 {count}개 문서가 집중되어 있습니다: {stems_str}")
            print(f"      -> 향후 단일 권위 가이드(Authoritative Guide)로 통합 압축 권장.")
    else:
        print("  * 파편화된 집중 마이크로 노트가 없습니다. 지식 밀도가 적절합니다.")
        
    print("\n[🏷️ 주요 기술 태그 분포]")
    for t, cnt in sorted(tag_counter.items(), key=lambda x: -x[1])[:8]:
        print(f"  - #{t}: {cnt}개 문서")
    print("=" * 60)

def query_wiki(keyword, lod=None, limit=5):
    docs = get_all_wiki_docs()
    stem_map = {d["stem"]: d for d in docs}
    
    # FTS5 인덱스 동기화 및 검색
    fts = FTSIndex()
    fts.sync_all(docs)
    results = fts.search(keyword, limit=limit)
    fts.close()
    
    print(f"=== [Wiki FTS5 Query] '{keyword}' 검색 결과 ({len(results)}건 매칭, LOD: {lod if lod is not None else 'Default'}) ===")
    if not results:
        print(f"일치하는 위키 문서를 찾지 못했습니다. ('{keyword}')")
        return
        
    for res in results:
        stem = res["stem"]
        d = stem_map.get(stem)
        if not d:
            continue
            
        score = res["score"]
        snippet = res.get("snippet", "")
        
        if lod == 0:
            # LOD 0: 메타데이터만 1줄로 출력 (~10 토큰)
            tags_str = ", ".join(d["tags"])
            print(f"[{d['type'].upper()}] [[{stem}]] {d['title']} | tags: [{tags_str}] | updated: {d['updated']}")
        elif lod == 1:
            # LOD 1: 에이전트 초고속 회상용 TL;DR / 해결책만 출력 (~100 토큰)
            print(f"\n📄 [[{stem}]] {d['title']} (분류: {d['type']}, 점수: {score})")
            print(f"   * 태그: {', '.join(d['tags'])}")
            print(f"   * 💡 요약 (LOD 1):\n{d['lod1']}")
            print(f"   * 출처: {', '.join(d['sources'])}")
        elif lod == 2:
            # LOD 2: 전체 문서 전문 출력
            print(f"\n{'=' * 60}")
            print(f"# [[{stem}]] {d['title']} (LOD 2 Full Document)")
            print(f"{'=' * 60}")
            print(d["raw_content"])
        else:
            # 기본 뷰: 균형 잡힌 카드 뷰
            print(f"\n📄 [[{stem}]] {d['title']} (분류: {d['type']}, BM25 점수: {score})")
            print(f"   * 태그: {', '.join(d['tags'])}")
            print(f"   * 요약: {d['summary']}")
            if snippet:
                clean_snippet = snippet.replace("<b>", "**").replace("</b>", "**")
                print(f"   * 매칭 스니펫: {clean_snippet}")
            print(f"   * 경로: {d['rel_path']}")

def ingest_knowledge(title, category, raw_source_content, wiki_body, tags=None, related=None):
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # CLI에서 전달된 이스케이프 개행 문자(\n)를 실제 개행으로 복원
    raw_source_content = raw_source_content.replace("\\n", "\n")
    wiki_body = wiki_body.replace("\\n", "\n")
    
    clean_title = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", title).strip("-").lower()
    if not clean_title:
        clean_title = f"doc-{datetime.date.today().strftime('%Y%m%d%H%M%S')}"
        
    # 1. 원본 저장 (sources/)
    source_filename = f"sources/{today}-{clean_title}.md"
    source_full_path = os.path.join(WIKI_ROOT, source_filename)
    source_text = f"# Source: {title}\nDate: {today}\nCategory: {category}\n\n{raw_source_content.strip()}\n"
    with open(source_full_path, "w", encoding="utf-8") as f:
        f.write(source_text)
    print(f"[Ingest] 1단계: 불변 원본 아카이빙 완료 -> {source_filename}")

    # 2. 위키 문서 생성 (wiki/<category>/<slug>.md)
    cat_dir = os.path.join(WIKI_ROOT, "wiki", category)
    os.makedirs(cat_dir, exist_ok=True)
    wiki_filename = os.path.join(cat_dir, f"{clean_title}.md")
    
    tags_list = [t.strip() for t in (tags or "").split(",") if t.strip()]
    if category not in tags_list:
        tags_list.append(category)
        
    related_list = [f"[[{r.strip()}]]" for r in (related or "").split(",") if r.strip()]
    
    type_map = {
        "concepts": "concept",
        "tools": "tool",
        "troubleshooting": "troubleshooting"
    }
    doc_type = type_map.get(category, "concept")
    
    tags_str = ", ".join(f'"{t}"' for t in tags_list)
    fm_lines = [
        "---",
        f'title: "{title}"',
        f'type: "{doc_type}"',
        f"tags: [{tags_str}]",
        f"sources:\n  - \"{source_filename}\"",
        f'updated: "{today}"'
    ]
    if related_list:
        fm_lines.append("related:")
        for rel in related_list:
            fm_lines.append(f'  - "{rel}"')
    fm_lines.append("---\n")
    
    full_doc = "\n".join(fm_lines) + wiki_body.strip() + "\n"
    with open(wiki_filename, "w", encoding="utf-8") as f:
        f.write(full_doc)
    print(f"[Ingest] 2단계: 위키 지식 문서 생성 완료 -> wiki/{category}/{clean_title}.md")

    # 3. 자동 색인 및 FTS5 인덱싱 (Reindex)
    reindex_wiki()
    print("[Ingest] 3단계: 색인(index.md), 서브 MOC 및 FTS5 동기화 완료")

    # 4. 로그 갱신 (log.md)
    log_change(title, "Ingested", clean_title)
    print("[Ingest] 4단계: 변경 로그(log.md) 기록 완료")

    # 5. 린터 무결성 검증 (Linter)
    print("[Ingest] 5단계: 무결성 검증 수행 중...")
    lint_code = run_linter()
    if lint_code != 0:
        print("[!] 린터 검증에서 오류가 발생했습니다. 확인이 필요합니다.")
        return 1

    # 6. Git 커밋
    git_commit(f"feat(wiki): ingest knowledge '{title}'")
    print("[Ingest] 6단계: Git 버전 아카이빙 완료")

    # 7. 디스코드 알림
    lod1 = extract_lod1(wiki_body)
    summary_text = lod1.split("\n")[0] if lod1 else title
    send_discord_notification(title, summary_text, category, f"wiki/{category}/{clean_title}.md")
    print(f"[Ingest] 7단계: 완료! 지식 베이스에 성공적으로 영구 축적되었습니다.")
    return 0

if __name__ == "__main__":
    # 서브커맨드 형태 지원 (e.g. wiki_manager.py ingest --title ... / wiki_manager.py lint)
    if len(sys.argv) > 1 and sys.argv[1] == "lint":
        sys.exit(run_linter())
    elif len(sys.argv) > 1 and sys.argv[1] == "reindex":
        reindex_wiki()
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "audit":
        audit_wiki()
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "query":
        sys.argv.pop(1)
        sys.argv.insert(1, "--action")
        sys.argv.insert(2, "query")
    elif len(sys.argv) > 1 and sys.argv[1] == "ingest":
        sys.argv.pop(1)
        sys.argv.insert(1, "--action")
        sys.argv.insert(2, "ingest")
        
    parser = argparse.ArgumentParser(description="Autonomous LLM Wiki Knowledge Engine")
    parser.add_argument("--action", choices=["commit", "notify", "sync", "init", "lint", "reindex", "audit", "query", "ingest"], default="commit")
    parser.add_argument("query_kw", nargs="?", default="", help="Positional search keyword for query")
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--summary", help="Document summary")
    parser.add_argument("--category", choices=["concepts", "tools", "troubleshooting"], help="Document category")
    parser.add_argument("--path", help="Relative file path")
    parser.add_argument("--source", help="Raw source content or path for ingest")
    parser.add_argument("--content", help="Wiki markdown content for ingest")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--related", help="Comma-separated related slugs")
    parser.add_argument("--keyword", help="Search keyword for query")
    parser.add_argument("--lod", type=int, choices=[0, 1, 2], help="Level of Detail: 0 (Metadata), 1 (TL;DR Summary), 2 (Full Body)")
    parser.add_argument("--limit", type=int, default=5, help="Max search results")
    
    args = parser.parse_args()
    
    if args.action == "lint":
        sys.exit(run_linter())
    elif args.action == "reindex":
        reindex_wiki()
    elif args.action == "audit":
        audit_wiki()
    elif args.action == "query":
        search_target = args.keyword or args.query_kw or args.title or ""
        query_wiki(search_target, lod=args.lod, limit=args.limit)
    elif args.action == "ingest":
        if not args.title or not args.category or not args.content:
            print("Error: --title, --category, and --content are required for ingest.")
            sys.exit(1)
        raw_src = args.source or f"Source reference for {args.title}"
        if os.path.isfile(raw_src):
            with open(raw_src, "r", encoding="utf-8") as sf:
                raw_src = sf.read()
        res = ingest_knowledge(args.title, args.category, raw_src, args.content, args.tags, args.related)
        sys.exit(res)
    elif args.action == "init":
        git_commit("feat: initialize LLM Wiki repository and seed docs")
        if args.summary:
            send_discord_notification(args.title or "초기 위키 구축 완료", args.summary, "System", "Documents/Wiki")
    elif args.action == "notify":
        send_discord_notification(args.title, args.summary, args.category or "General", args.path or "")
    elif args.action == "commit":
        git_commit(f"docs: update wiki ({args.title or 'auto-update'})")
