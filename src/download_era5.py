"""Download ERA5-Land monthly means for Algeria.

Steps
-----
1. Read the Algeria/wilaya polygons from data/geo/dz.json and combine them
   into one national boundary.

2. Derive the smallest enclosing CDS bounding box in API order N/W/S/E [37.1, -8.7, 18.9, 12].
   The box only limits the download; it is not the final study-area mask.

3. Select either all listed monthly variables or the 12 project variables,
   then request the available months one year at a time from the CDS.

4. Reuse non-empty annual downloads. If a full-year request fails, retry
   variable by variable and report variables the CDS rejects.
   
5. Save the downloaded archives in data/raw/. ERA5 may package multiple
   NetCDF members inside a ZIP archive even when the filename ends in .nc.

"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import date
from pathlib import Path

import cdsapi
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
DATASET = "reanalysis-era5-land-monthly-means"

# Variables required by the project statement (11 inputs + the target).
VARIABLES_PROJECT = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_latent_heat_flux",
    "surface_net_solar_radiation",
    "surface_net_thermal_radiation",
    "surface_sensible_heat_flux",
    "runoff",
    "total_evaporation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_pressure",
    "total_precipitation",
]

# Every monthly ERA5-Land variable (to explore and select features later).
VARIABLES_ALL = VARIABLES_PROJECT + [
    "skin_temperature",
    "skin_reservoir_content",
    "forecast_albedo",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "potential_evaporation",
    "evaporation_from_bare_soil",
    "evaporation_from_open_water_surfaces_excluding_oceans",
    "evaporation_from_the_top_of_canopy",
    "evaporation_from_vegetation_transpiration",
    "surface_runoff",
    "sub_surface_runoff",
    "soil_temperature_level_1",
    "soil_temperature_level_2",
    "soil_temperature_level_3",
    "soil_temperature_level_4",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
    "volumetric_soil_water_layer_3",
    "volumetric_soil_water_layer_4",
    "leaf_area_index_high_vegetation",
    "leaf_area_index_low_vegetation",
    "snow_albedo",
    "snow_cover",
    "snow_density",
    "snow_depth",
    "snow_depth_water_equivalent",
    "snow_evaporation",
    "snowfall",
    "snowmelt",
    "temperature_of_snow_layer",
    "lake_bottom_temperature",
    "lake_ice_depth",
    "lake_ice_temperature",
    "lake_mix_layer_depth",
    "lake_mix_layer_temperature",
    "lake_shape_factor",
    "lake_total_layer_temperature",
    # Additional static or land-cover fields offered by the monthly CDS form.
    "high_vegetation_cover",
    "glacier_mask",
    "lake_cover",
    "low_vegetation_cover",
    "lake_total_depth",
    "geopotential",
    "land_sea_mask",
    "soil_type",
    "type_of_high_vegetation",
    "type_of_low_vegetation",
]
VARIABLE_SETS = {"project": VARIABLES_PROJECT, "all": VARIABLES_ALL}


# ----------------------------------------------------------------- helpers
def latest_expected_month(lag_months: int, today: date | None = None) -> date:
    """Last month assumed to be published (today minus a safety lag)."""
    today = today or date.today()
    month_index = today.year * 12 + today.month - 1 - lag_months
    return date(month_index // 12, month_index % 12 + 1, 1)


def get_algeria_geometry(geojson_path: Path):
    """Merge the 58 wilaya polygons into one Algeria geometry."""
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    polygons = [shape(feature["geometry"]) for feature in payload["features"]]
    if not polygons:
        raise ValueError(f"No boundary features in {geojson_path}")
    return unary_union(polygons)


def build_area(geometry) -> list[float]:
    """Bounding box [N, W, S, E], rounded outwards to the 0.1 degree grid."""
    west, south, east, north = geometry.bounds
    return [
        round(math.ceil(north * 10) / 10, 1),
        round(math.floor(west * 10) / 10, 1),
        round(math.floor(south * 10) / 10, 1),
        round(math.ceil(east * 10) / 10, 1),
    ]


def is_valid_file(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


# ---------------------------------------------------------------- download
def retrieve(client, request: dict, target: Path) -> None:
    """Download to a temporary name, then rename: no half-written files."""
    tmp = target.with_suffix(".part")
    client.retrieve(DATASET, request, str(tmp))
    tmp.replace(target)


def make_request(variables: list[str], year: int, months: list[str], area: list[float]) -> dict:
    return {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": variables,
        "year": [str(year)],
        "month": months,
        "time": ["00:00"],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": area,
    }


def download_year(client, year, months, variables, area, raw_dir, bad_vars) -> list[Path]:
    """Download one year. If the full request fails, retry variable by variable."""
    variables = [v for v in variables if v not in bad_vars]
    tag = hashlib.md5(",".join(sorted(variables)).encode()).hexdigest()[:8]
    base = f"era5_land_{year}_{months[0]}-{months[-1]}"
    target = raw_dir / f"{base}_{tag}.nc"

    if is_valid_file(target):
        print(f"Using existing {target.name}")
        return [target]

    try:
        print(f"Requesting {year}, months {months[0]}-{months[-1]}, "
              f"{len(variables)} variables, area N/W/S/E={area}")
        retrieve(client, make_request(variables, year, months, area), target)
        return [target]
    except Exception as exc:  # noqa: BLE001
        print(f"Full request failed ({exc}). Retrying variable by variable...")

    paths, failures = [], 0
    for var in variables:
        path = raw_dir / f"{base}_{var}.nc"
        if is_valid_file(path):
            paths.append(path)
            continue
        try:
            retrieve(client, make_request([var], year, months, area), path)
            paths.append(path)
            failures = 0
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAILED] {var}: {exc}")
            bad_vars.add(var)
            failures += 1
            if failures >= 3 and not paths:
                raise RuntimeError(
                    "Several requests failed in a row. Check your CDS  and licence "
                    "acceptance, your network, or increase --lag-months."
                ) from exc
    return paths


# -------------------------------------------------------------------- main
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=None,
                        help="Last year to retrieve (default: latest published month)")
    parser.add_argument("--lag-months", type=int, default=3,
                        help="Safety lag before the latest month is requested (default: 3)")
    parser.add_argument("--variables", choices=VARIABLE_SETS, default="all",
                        help="'all' = every monthly variable, 'project' = the 12 required ones")
    args = parser.parse_args()
    if args.lag_months < 0:
        parser.error("--lag-months must be >= 0")
    return args


def main() -> None:
    args = parse_args()

    latest = latest_expected_month(args.lag_months)
    requested_end_year = args.end_year or latest.year
    if requested_end_year < args.start_year:
        raise SystemExit("--end-year must be >= --start-year")
    last_year, last_month = min((requested_end_year, 12), (latest.year, latest.month))
    if (last_year, last_month) < (args.start_year, 1):
        raise SystemExit("The selected period ends before --start-year")

    raw_dir = ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    geometry = get_algeria_geometry(ROOT / "data" / "geo" / "dz.json")
    area = build_area(geometry)

    client = cdsapi.Client()
    variables = VARIABLE_SETS[args.variables]
    bad_vars: set[str] = set()
    files_by_year: list[list[Path]] = []
    for year in range(args.start_year, last_year + 1):
        months = [f"{m:02d}" for m in range(1, 13) if (year, m) <= (last_year, last_month)]
        files_by_year.append(download_year(client, year, months, variables, area, raw_dir, bad_vars))

    if bad_vars:
        print(f"\nVariables rejected by the CDS (check their names): {sorted(bad_vars)}")
    downloaded = [path for year_files in files_by_year for path in year_files]
    print(f"\nRaw download complete: {len(downloaded)} file(s) in {raw_dir}")
    print("Next step: python src/merge_era5.py")


if __name__ == "__main__":
    main()
