from __future__ import annotations

import argparse
import json
import re
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tft_ai_coach.paths import DDRAGON_DIR, ensure_dirs

VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
CDN_ROOT = "https://ddragon.leagueoflegends.com/cdn"
STATIC_FILES = {
    "champions": "tft-champion.json",
    "items": "tft-item.json",
    "traits": "tft-trait.json",
    "augments": "tft-augments.json",
}


@dataclass(slots=True)
class StaticRecord:
    id: str
    name: str
    kind: str
    image_group: str = ""
    image_file: str = ""
    cost: int | None = None
    tier: int | None = None
    description: str = ""


def _read_json_url(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as response:
        path.write_bytes(response.read())


def latest_version() -> str:
    versions = _read_json_url(VERSIONS_URL)
    if not versions:
        raise RuntimeError("Data Dragon returned no versions")
    return versions[0]


def _extract_set_number(identifier: str) -> int | None:
    match = re.search(r"TFT(\d+)_", identifier)
    if match:
        return int(match.group(1))
    return None


def _current_set_id(champions: dict[str, Any]) -> str:
    set_numbers: list[int] = []
    for record in champions.values():
        set_number = _extract_set_number(record.get("id", ""))
        if set_number is not None:
            set_numbers.append(set_number)
    if not set_numbers:
        return ""
    return f"TFT{max(set_numbers)}"


def _record_from_raw(kind: str, raw: dict[str, Any]) -> StaticRecord:
    image = raw.get("image") or {}
    return StaticRecord(
        id=raw.get("id", ""),
        name=raw.get("name", ""),
        kind=kind,
        image_group=image.get("group", ""),
        image_file=image.get("full", ""),
        cost=raw.get("cost"),
        tier=raw.get("tier"),
        description=raw.get("description", ""),
    )


def _belongs_to_current_set(record: StaticRecord, current_set: str) -> bool:
    if not current_set:
        return True
    if record.kind == "champions" and _is_non_shop_champion(record):
        return False
    if record.kind == "augments":
        return current_set in record.id or _extract_set_number(record.id) is None
    if record.kind == "items":
        return record.id.startswith("TFT_Item_") or current_set in record.id
    return current_set in record.id


def _is_non_shop_champion(record: StaticRecord) -> bool:
    if record.cost is None or record.cost <= 0:
        return True
    blocked_fragments = ["FakeUnit", "Enemy_", "Minion", "TraitClone"]
    return any(fragment in record.id for fragment in blocked_fragments)


def update_static_data(
    version: str | None = None,
    download_icons: bool = False,
    icon_kinds: set[str] | None = None,
) -> dict[str, Any]:
    ensure_dirs()
    version = version or latest_version()
    version_dir = DDRAGON_DIR / version
    raw_dir = version_dir / "raw"
    icon_dir = version_dir / "icons"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_payloads: dict[str, Any] = {}
    for kind, filename in STATIC_FILES.items():
        url = f"{CDN_ROOT}/{version}/data/en_US/{filename}"
        payload = _read_json_url(url)
        raw_payloads[kind] = payload
        (raw_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    current_set = _current_set_id(raw_payloads["champions"].get("data", {}))
    normalized: dict[str, list[dict[str, Any]]] = {}
    for kind, payload in raw_payloads.items():
        records = [_record_from_raw(kind, raw) for raw in payload.get("data", {}).values()]
        if kind in {"champions", "traits", "augments", "items"}:
            records = [record for record in records if _belongs_to_current_set(record, current_set)]
        normalized[kind] = [asdict(record) for record in sorted(records, key=lambda item: (item.cost or 0, item.name))]

    index = {
        "version": version,
        "set_id": current_set,
        "source": "Riot Data Dragon",
        "records": normalized,
    }
    (version_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    (DDRAGON_DIR / "current.json").write_text(json.dumps({"version": version}, indent=2), encoding="utf-8")

    if download_icons:
        for kind, records in normalized.items():
            if icon_kinds is not None and kind not in icon_kinds:
                continue
            for record in records:
                image_group = record.get("image_group")
                image_file = record.get("image_file")
                if not image_group or not image_file:
                    continue
                icon_path = icon_dir / image_group / image_file
                if icon_path.exists():
                    continue
                url = f"{CDN_ROOT}/{version}/img/{image_group}/{image_file}"
                try:
                    _download(url, icon_path)
                except Exception:
                    continue

    return index


def load_current_index() -> dict[str, Any]:
    pointer = DDRAGON_DIR / "current.json"
    if not pointer.exists():
        return update_static_data(download_icons=False)
    version = json.loads(pointer.read_text(encoding="utf-8"))["version"]
    index_path = DDRAGON_DIR / version / "index.json"
    if not index_path.exists():
        return update_static_data(version=version, download_icons=False)
    return json.loads(index_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Update TFT static data from Data Dragon.")
    parser.add_argument("--version", default=None)
    parser.add_argument("--download-icons", action="store_true")
    parser.add_argument(
        "--icon-kind",
        action="append",
        choices=sorted(STATIC_FILES),
        help="Limit icon downloads to one data kind. Can be passed more than once.",
    )
    args = parser.parse_args()
    icon_kinds = set(args.icon_kind) if args.icon_kind else None
    index = update_static_data(version=args.version, download_icons=args.download_icons, icon_kinds=icon_kinds)
    print(f"Updated TFT data: patch={index['version']} set={index['set_id']}")
    for kind, records in index["records"].items():
        print(f"- {kind}: {len(records)}")


if __name__ == "__main__":
    main()
