"""Download OSDU API specifications and store them as JSON files.

This script fetches OpenAPI documents from a predefined set of URLs, converts
them to JSON (when necessary), and writes the normalized JSON payloads to the
local filesystem.

The default behaviour downloads every known specification into the
``downloads`` directory that lives alongside this script. Use the command-line
options to alter the output directory or limit the download set.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

import requests
import yaml


DEFAULT_URLS: dict[str, str] = {
	"dataset_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/dataset_openapi.yaml",
	"entitlements_v2": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/entitlements_openapi.yaml",
	"file_v2": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/file_service_openapi.yaml",
	"eds": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/eds_openapi.yaml",
	"indexer_v2": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/indexer_openapi.yaml",
	"legal_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/compliance_openapi.yaml",
	"notification_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/notification_openapi.yaml",
	"partition_v1": "https://contoso.energy.azure.com/api/partition/v1/api-docs",
	"petrel_dms": "https://contoso.energy.azure.com/api/petreldms/docs/v1/swagger.json",
	"register_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/register_openapi.yaml",
	"schema_service_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/schema_openapi.yaml",
	"search_v2": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/search_openapi.yaml",
	"secret_v2": "https://community.opengroup.org/osdu/platform/security-and-compliance/secret/-/raw/main/docs/api/v2_openapi.json",
	"storage_v2": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/storage_openapi.yaml",
	"crs_converter_v4": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/crs_converter_openapi.yaml",
	"crs_catalog_v3": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/crs_catalog_v3_openapi.yaml",
	"unit_v3": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/unit_openapi.yaml",
	"schema_upgrade": "https://community.opengroup.org/osdu/platform/system/reference/schema-upgrade/-/raw/main/Docs/openapi.json",
	"workflow_v1": "https://raw.githubusercontent.com/microsoft/adme-samples/refs/heads/main/rest-apis/M25/ingestion_worflow_openapi.yaml",
	"seismic_file_metadata": "https://github.com/microsoft/adme-samples/blob/main/rest-apis/M25/seismic_file_metadata_openapi.yaml",
	"seismic_ddms": "https://raw.githubusercontent.com/microsoft/adme-samples/main/rest-apis/M25/seismic_ddms_openapi.yaml",
	"os_wellbore_ddms": "https://raw.githubusercontent.com/microsoft/adme-samples/main/rest-apis/M25/wellbore_ddms_openapi.yaml",
	"rafs_ddms": "https://contoso.energy.azure.com/api/rafs-ddms/openapi.json",
	"well_delivery": "https://raw.githubusercontent.com/microsoft/adme-samples/main/rest-apis/M25/welldelivery_ddms_openapi.yaml",
	"reservoir": "https://github.com/microsoft/adme-samples/blob/main/rest-apis/M25/reservoir_openapi.yaml",
}


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "downloads"
REQUEST_TIMEOUT_SECONDS = 60


# Accept JSON or YAML responses from the various API endpoints.
HEADERS = {
	"Accept": "application/json, application/yaml, text/yaml, */*",
	"User-Agent": "ADME-SpecFetcher/1.0",
}


def _normalise_github_blob(url: str) -> str:
	"""Transform GitHub blob URLs into their raw counterparts."""

	if "github.com" not in url:
		return url

	# Support both the canonical blob URLs and shorthand forms.
	blob_pattern = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)")
	match = blob_pattern.fullmatch(url)
	if not match:
		return url

	owner = match.group("owner")
	repo = match.group("repo")
	branch = match.group("branch")
	path = match.group("path")
	return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def _load_payload(raw_text: str) -> Any:
	"""Parse raw API specification content into a JSON-serialisable object."""

	try:
		parsed = json.loads(raw_text)
	except json.JSONDecodeError:
		parsed = _load_yaml_with_fallback(raw_text)

	if parsed is None:
		raise ValueError("Specification is empty")

	if not isinstance(parsed, (dict, list)):
		raise TypeError(
			"Parsed specification must be a JSON object or array, got "
			f"{type(parsed).__name__}"
		)

	return parsed


def _write_json(content: Any, output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8") as handle:
		json.dump(content, handle, indent=2, ensure_ascii=False, cls=_EnhancedJSONEncoder)
		handle.write("\n")


class _EnhancedJSONEncoder(json.JSONEncoder):
	"""JSON encoder that knows how to serialise dates produced by PyYAML."""

	def default(self, obj: Any) -> Any:  # type: ignore[override]
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		return super().default(obj)


def _load_yaml_with_fallback(raw_text: str) -> Any:
	"""Attempt to parse YAML, retrying with tab-normalised content when needed."""

	try:
		return yaml.safe_load(raw_text)
	except yaml.YAMLError as first_error:
		if "\t" not in raw_text:
			raise

		normalised = _normalise_yaml_tabs(raw_text)
		try:
			return yaml.safe_load(normalised)
		except yaml.YAMLError as second_error:
			raise second_error from first_error


def _normalise_yaml_tabs(text: str) -> str:
	"""Convert tab characters to YAML-friendly sequences."""

	result: list[str] = []
	in_single = False
	in_double = False
	length = len(text)
	i = 0
	while i < length:
		ch = text[i]
		if ch == "'" and not in_double:
			if in_single:
				if i + 1 < length and text[i + 1] == "'":
					result.append("''")
					i += 2
					continue
				in_single = False
				result.append("'")
				i += 1
				continue
			in_single = True
			result.append("'")
			i += 1
			continue
		if ch == '"' and not in_single:
			if _preceded_by_odd_backslashes(text, i):
				result.append(ch)
				i += 1
				continue
			in_double = not in_double
			result.append(ch)
			i += 1
			continue
		if ch == "\t":
			if in_double:
				result.append("\\t")
			else:
				result.append("  ")
			i += 1
			continue
		result.append(ch)
		if ch == "\n":
			# Quoted scalars can span lines; retain state.
			pass
		i += 1
	return "".join(result)


def _preceded_by_odd_backslashes(text: str, index: int) -> bool:
	"""Return True if the character at *index* is escaped by an odd number of backslashes."""

	count = 0
	pos = index - 1
	while pos >= 0 and text[pos] == "\\":
		count += 1
		pos -= 1
	return count % 2 == 1


def fetch_spec(name: str, url: str, output_dir: Path, overwrite: bool = False) -> Path:
	"""Download and persist a single specification."""

	normalised_url = _normalise_github_blob(url)
	output_path = output_dir / f"{name}.json"

	if output_path.exists() and not overwrite:
		logging.info("Skipping %s – file already exists", name)
		return output_path

	logging.info("Downloading %s from %s", name, normalised_url)
	response = requests.get(normalised_url, timeout=REQUEST_TIMEOUT_SECONDS, headers=HEADERS)
	response.raise_for_status()

	payload = _load_payload(response.text)
	_write_json(payload, output_path)
	logging.info("Saved %s (%s bytes)", output_path, output_path.stat().st_size)
	return output_path


def fetch_specs(
	targets: Mapping[str, str],
	output_dir: Path,
	overwrite: bool = False,
) -> list[Path]:
	"""Download a batch of specifications into ``output_dir``."""

	results: list[Path] = []
	for name, url in targets.items():
		try:
			results.append(fetch_spec(name, url, output_dir, overwrite=overwrite))
		except Exception as exc:  # noqa: BLE001 - log and continue to the next spec.
			logging.error("Failed to fetch %s: %s", name, exc)
	return results


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=DEFAULT_OUTPUT_DIR,
		help="Directory to store the downloaded JSON specifications (default: %(default)s)",
	)
	parser.add_argument(
		"--overwrite",
		action="store_true",
		help="Overwrite files that already exist.",
	)
	parser.add_argument(
		"--only",
		metavar="SPEC",
		nargs="*",
		help="Names of specific specs to download (default: all).",
	)
	parser.add_argument(
		"--list",
		action="store_true",
		help="List available specification keys and exit.",
	)
	parser.add_argument(
		"--verbose",
		action="store_true",
		help="Enable debug logging output.",
	)
	return parser.parse_args(list(argv))


def configure_logging(verbose: bool) -> None:
	level = logging.DEBUG if verbose else logging.INFO
	logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: Iterable[str] | None = None) -> int:
	args = parse_args(argv or sys.argv[1:])
	configure_logging(args.verbose)

	if args.list:
		print("Available specifications:")
		for name in DEFAULT_URLS:
			print(f"- {name}")
		return 0

	if args.only:
		missing = sorted(set(args.only) - set(DEFAULT_URLS))
		if missing:
			logging.error("Unknown specification keys requested: %s", ", ".join(missing))
			return 1
		target_urls = {name: DEFAULT_URLS[name] for name in args.only}
	else:
		target_urls = DEFAULT_URLS

	logging.info("Fetching %d specification(s) into %s", len(target_urls), args.output_dir)
	fetched = fetch_specs(target_urls, args.output_dir, overwrite=args.overwrite)
	logging.info("Completed. %d specification(s) downloaded.", len(fetched))
	return 0 if fetched else 2


if __name__ == "__main__":
	raise SystemExit(main())
