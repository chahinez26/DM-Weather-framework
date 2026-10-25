"""Extract, merge and prepare the downloaded ERA5-Land data for Algeria.

6. Run src/merge_era5.py to extract and merge those members, mask the grid
   with the Algeria polygons, aggregate by the requested factor (*4), and save
   the analysis-ready NetCDF file into data/processed/.

The CDS may return a ZIP archive containing a main monthly NetCDF plus
separate NetCDF files for static fields, even when the downloaded filename
ends in .nc. This script handles both those ZIP files and plain NetCDF files.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import xarray as xr
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
DATASET = "reanalysis-era5-land-monthly-means"

# CDS uses abbreviated filenames for these static fields. Use descriptive
# variable names in the merged dataset for the fields with categorical codes.
STATIC_NAMES = {
    "cicecap": "glacier_mask",
    "clake": "lake_cover",
    "cvh": "high_vegetation_cover",
    "cvl": "low_vegetation_cover",
    "dl": "lake_total_depth",
    "geo": "geopotential",
    "lsm": "land_sea_mask",
    "slt": "soil_type",
    "tvh": "type_of_high_vegetation",
    "tvl": "type_of_low_vegetation",
}
CATEGORICAL_VARIABLES = {
    "soil_type",
    "type_of_high_vegetation",
    "type_of_low_vegetation",
}


def coordinate_names(ds: xr.Dataset) -> xr.Dataset:
    """Normalize common CDS coordinate spellings and the time dimension."""
    rename = {}
    for name in ds.variables:
        low = name.lower()
        if low in {"lat", "latitude"} and name != "latitude":
            rename[name] = "latitude"
        elif low in {"lon", "longitude"} and name != "longitude":
            rename[name] = "longitude"
        elif low == "valid_time" and name != "time":
            rename[name] = "time"
    if rename:
        ds = ds.rename(rename)
    ds = ds.drop_vars(["number", "expver"], errors="ignore")
    # Some ERA5 static fields use longitudes in 0..360 and float32 coordinates,
    # while the monthly file uses -180..180 and decimal tenths. Normalize both
    # to the same 0.1-degree grid before merging.
    if "latitude" in ds.coords:
        ds = ds.assign_coords(latitude=np.round(ds.latitude.astype(float), 1))
    if "longitude" in ds.coords:
        longitude = ds.longitude.astype(float)
        longitude = xr.where(longitude > 180, longitude - 360, longitude)
        ds = ds.assign_coords(longitude=np.round(longitude, 1))
    if "latitude" in ds.coords and "longitude" in ds.coords:
        ds = ds.sortby("latitude").sortby("longitude")
    return ds


def load_member(path: Path) -> xr.Dataset:
    """Load a NetCDF member into memory before its temporary file is removed."""
    with xr.open_dataset(path) as opened:
        ds = opened.load()
    return coordinate_names(ds)


def classify_member(path: Path, ds: xr.Dataset) -> str:
    """Classify one downloaded NetCDF member as dynamic or static."""
    stem = path.name.split(".", maxsplit=1)[0]
    if stem in STATIC_NAMES:
        return "static"
    if "data_stream-moda" in path.name or "time" in ds.dims:
        return "dynamic"
    return "static"


def rename_static(path: Path, ds: xr.Dataset) -> xr.Dataset:
    """Rename a one-variable static member to its CDS long name when known."""
    stem = path.name.split(".", maxsplit=1)[0]
    target = STATIC_NAMES.get(stem)
    variables = list(ds.data_vars)
    if target and len(variables) == 1 and variables[0] != target:
        ds = ds.rename({variables[0]: target})
    # Static ERA5 fields have no meaningful time axis; remove singleton axes.
    squeeze_dims = [name for name, size in ds.sizes.items() if size == 1]
    return ds.squeeze(dim=squeeze_dims, drop=True) if squeeze_dims else ds


def open_raw_file(path: Path, temp_root: Path,
                  static_already_loaded: set[str]) -> tuple[list[xr.Dataset], list[xr.Dataset]]:
    """Read the dynamic and static NetCDF datasets in one raw download."""
    dynamic_parts, static_parts = [], []
    if zipfile.is_zipfile(path):
        with tempfile.TemporaryDirectory(prefix=f"{path.stem}_", dir=temp_root) as folder:
            folder = Path(folder)
            with zipfile.ZipFile(path) as archive:
                members = [name for name in archive.namelist()
                           if name.lower().endswith(".nc") and not name.endswith("/")]
                for member in members:
                    stem = Path(member).name.split(".", maxsplit=1)[0]
                    known_static_name = STATIC_NAMES.get(stem)
                    if known_static_name in static_already_loaded:
                        continue
                    # Ignore paths in archive names; extract each NetCDF by basename.
                    target = folder / Path(member).name
                    with archive.open(member) as src, target.open("wb") as dst:
                        dst.write(src.read())
                    ds = load_member(target)
                    if classify_member(target, ds) == "dynamic":
                        dynamic_parts.append(ds)
                    else:
                        static_parts.append(rename_static(target, ds))
    else:
        ds = load_member(path)
        if classify_member(path, ds) == "dynamic":
            dynamic_parts.append(ds)
        else:
            static_parts.append(rename_static(path, ds))
    if not dynamic_parts and not static_parts:
        raise ValueError(f"No NetCDF files found inside {path}")
    return dynamic_parts, static_parts


def get_algeria_geometry(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    geometries = [shape(feature["geometry"]) for feature in payload["features"]]
    if not geometries:
        raise ValueError(f"No boundary features found in {path}")
    return unary_union(geometries)


def merge_parts(parts: list[xr.Dataset]) -> xr.Dataset:
    if len(parts) == 1:
        return parts[0]
    return xr.merge(parts, compat="override", join="exact", combine_attrs="override")


def majority_vote(values, axis):
    """Mode over the spatial sub-cell axes, omitting NaN values."""
    from scipy.stats import mode

    axes = (axis,) if isinstance(axis, int) else tuple(axis)
    dest = tuple(range(values.ndim - len(axes), values.ndim))
    values = np.moveaxis(values, axes, dest)
    values = values.reshape(*values.shape[:-len(axes)], -1)
    return mode(values, axis=-1, nan_policy="omit", keepdims=False).mode


def mask_algeria(ds: xr.Dataset, geometry) -> xr.Dataset:
    if "latitude" not in ds.coords or "longitude" not in ds.coords:
        raise ValueError(f"Missing latitude/longitude coordinates: {list(ds.coords)}")
    lon, lat = np.meshgrid(ds.longitude.values, ds.latitude.values)
    inside = contains_xy(geometry, lon, lat)
    mask = xr.DataArray(inside, coords={"latitude": ds.latitude, "longitude": ds.longitude},
                        dims=("latitude", "longitude"))
    return ds.where(mask)


def aggregate(ds: xr.Dataset, factor: int) -> xr.Dataset:
    if factor == 1:
        return ds
    result = ds.coarsen(latitude=factor, longitude=factor, boundary="pad").reduce(np.nanmean)
    for name in CATEGORICAL_VARIABLES.intersection(ds.data_vars):
        result[name] = ds[name].coarsen(
            latitude=factor, longitude=factor, boundary="pad"
        ).reduce(majority_vote)
    return result


def parse_year(path: Path) -> int:
    match = re.search(r"era5_land_(\d{4})_", path.name)
    if not match:
        raise ValueError(f"Can't find the year in raw filename: {path.name}")
    return int(match.group(1))


def merge_raw_files(files: list[Path], temp_root: Path) -> xr.Dataset:
    by_year: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        by_year[parse_year(path)].append(path)

    yearly_dynamic = []
    static_by_name: dict[str, xr.DataArray] = {}
    static_attrs: dict[str, dict] = {}

    # Temporary extraction folders live under the scratch directory and are
    # removed after each archive has been loaded into memory.
    for year in sorted(by_year):
        year_dynamic_parts = []
        for raw_path in sorted(by_year[year]):
            dynamic_parts, static_parts = open_raw_file(
                raw_path, temp_root, set(static_by_name)
            )
            year_dynamic_parts.extend(dynamic_parts)
            for part in static_parts:
                for name, array in part.data_vars.items():
                    if name not in static_by_name:
                        static_by_name[name] = array
                        static_attrs[name] = dict(part.attrs)
        if year_dynamic_parts:
            yearly_dynamic.append((year, merge_parts(year_dynamic_parts)))

    if not yearly_dynamic:
        raise ValueError("No time-varying monthly NetCDF data found in data/raw")

    annual_sets = [ds for _, ds in yearly_dynamic]
    time_dim = "time" if "time" in annual_sets[0].dims else None
    if time_dim is None:
        raise ValueError(f"No monthly time dimension in dataset: {dict(annual_sets[0].sizes)}")
    dynamic = xr.concat(annual_sets, dim=time_dim, data_vars="all", coords="minimal",
                        compat="override", join="outer", combine_attrs="override")
    dynamic = dynamic.sortby(time_dim)

    if static_by_name:
        static = xr.Dataset(static_by_name, attrs={"source": "ERA5-Land static fields"})
        for name, attrs in static_attrs.items():
            static[name].attrs.update(attrs)
        dynamic = xr.merge([dynamic, static], compat="override", join="exact",
                           combine_attrs="override")
    return dynamic


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factor", type=int, default=4,
                        help="Spatial aggregation factor on each axis (default: 4)")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.factor < 1:
        parser.error("--factor must be at least 1")

    files = sorted(args.raw_dir.glob("era5_land_*.nc"))
    if not files:
        raise SystemExit(f"No raw ERA5-Land files found in {args.raw_dir}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # Keep temporary extracted members beside the ignored raw archives.
    temp_root = RAW_DIR
    geometry = get_algeria_geometry(ROOT / "data" / "geo" / "dz.json")
    ds = merge_raw_files(files, temp_root)
    ds = ds.sortby("latitude").sortby("longitude")
    ds = mask_algeria(ds, geometry)
    ds = aggregate(ds, args.factor)

    first = str(ds.time.values[0])[:7]
    last = str(ds.time.values[-1])[:7]
    ds.attrs.update({
        "source": "Copernicus Climate Data Store, ERA5-Land monthly averaged reanalysis",
        "source_dataset": DATASET,
        "study_area": "Algeria; polygon mask from data/geo/dz.json (SimpleMaps)",
        "spatial_aggregation": f"mean of {args.factor}x{args.factor} source grid cells; categorical classes use mode",
        "source_grid_resolution": "0.1 degree",
        "time_period": f"{first} to {last}",
    })
    output = args.output or PROCESSED_DIR / f"era5_land_algeria_monthly_{first}_{last}_all.nc"
    output.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output)

    print(f"Saved {output}")
    print(f"  months: {ds.sizes['time']}; grid: {ds.sizes['latitude']} x {ds.sizes['longitude']}; "
          f"variables: {len(ds.data_vars)}")


if __name__ == "__main__":
    main()
