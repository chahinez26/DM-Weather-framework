# ============================================================
# 03_preprocessing.py : correction ECMWF (2022-2024) + valeurs aberrantes
# Format "# %%" : chaque bloc = une cellule de notebook (VS Code / Jupyter).
# Réutilise les noms du notebook 01 (BASE, SHP, AREA, FACTOR, VARS, load_year, client).
# ============================================================

# %% 0. Configuration
import os, glob, math, zipfile, tempfile
import numpy as np, pandas as pd, xarray as xr, geopandas as gpd
import matplotlib.pyplot as plt
from shapely import contains_xy
from shapely.ops import unary_union

BASE    = r"C:\Users\chahi\Desktop\DM-Weather-framework\data"   # adapte (comme dans le notebook 01)
DATA_DIR, OUT_DIR = f"{BASE}/data_nc", f"{BASE}/processed"
SHP     = f"{BASE}/dz_shp/dz.shp"
FACTOR  = 2
VARS    = ["t2m","d2m","sp","u10","v10","slhf","sshf","ssr","str","e","ro","tp"]

# Les 7 variables accumulées touchées par l'anomalie ECMWF (sept. 2022 - fév. 2024)
ACC_VARS = ["slhf","sshf","ssr","str","e","ro","tp"]
ACC_CDS  = ["surface_latent_heat_flux","surface_sensible_heat_flux","surface_net_solar_radiation",
            "surface_net_thermal_radiation","total_evaporation","runoff","total_precipitation"]
FIX_MONTHS = pd.date_range("2022-09-01", "2024-02-01", freq="MS")      # 18 mois à remplacer
CHECK_YEAR = 2021                                                       # année saine pour valider

gdf = gpd.read_file(SHP).to_crs(epsg=4326)
geometry = unary_union(gdf.dissolve().geometry)
west, south, east, north = gdf.dissolve().total_bounds
AREA = [round(math.ceil(north*10)/10,1), round(math.floor(west*10)/10,1),
        round(math.floor(south*10)/10,1), round(math.ceil(east*10)/10,1)]

# %% 0b. Client CDS (le script est autonome : plus besoin du notebook 01)
import os
import cdsapi
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("figures", exist_ok=True)

# Clé CDS : variable d'environnement CDS_KEY si elle existe,
# sinon lecture automatique du fichier ~/.cdsapirc (C:\\Users\\chahi\\.cdsapirc)
client = None

def get_client():
    global client
    if client is None:
        key = os.environ.get("CDS_KEY")
        client = (cdsapi.Client(url="https://cds.climate.copernicus.eu/api", key=key)
                  if key else cdsapi.Client())
    return client

# %% 1. Téléchargement du produit "by hour of day" (heure 00:00 = accumulation sur 24 h)
def download_byhour(year, months):
    target = f"{DATA_DIR}/byhour_{year}_{months[0]}-{months[-1]}.nc"
    if os.path.exists(target) and os.path.getsize(target) > 0:
        return target
    get_client().retrieve(
        "reanalysis-era5-land-monthly-means",
        {"product_type": ["monthly_averaged_reanalysis_by_hour_of_day"],   # vérifie ce nom via « Show API request »
         "variable": ACC_CDS, "year": [str(year)], "month": months,
         "time": ["00:00"], "area": AREA,
         "data_format": "netcdf", "download_format": "unarchived"},
        target + ".part")
    os.replace(target + ".part", target)
    return target

jobs = {2022: [f"{m:02d}" for m in range(9, 13)],      # sept-déc 2022
        2023: [f"{m:02d}" for m in range(1, 13)],      # 2023 entière
        2024: ["01", "02"],                            # janv-fév 2024
        CHECK_YEAR: [f"{m:02d}" for m in range(1, 13)]}  # année saine, pour la validation
byhour_files = {y: download_byhour(y, ms) for y, ms in jobs.items()}

# %% 2. Mêmes traitements spatiaux que le notebook 01 (masque natif puis blocs FACTOR x FACTOR)
def open_member(path):
    with xr.open_dataset(path) as o:
        ds = o.load()
    if "valid_time" in ds.coords:
        ds = ds.rename({"valid_time": "time"})
    return ds.drop_vars(["number", "expver"], errors="ignore")

def load_byhour(path):
    parts = []
    if zipfile.is_zipfile(path):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith(".nc"):
                    z.extract(n, tmp); parts.append(open_member(os.path.join(tmp, n)))
    else:
        parts.append(open_member(path))
    ds = xr.merge(parts, compat="no_conflicts", join="outer", combine_attrs="drop")
    for d in ("step", "hour", "time_of_day"):            # dimension d'heure éventuelle (une seule valeur : 00:00)
        if d in ds.dims and ds.sizes[d] == 1:
            ds = ds.isel({d: 0}, drop=True)
    ds = ds.assign_coords(latitude=np.round(ds.latitude.astype(float), 1),
                          longitude=np.round(ds.longitude.astype(float), 1))
    ds["time"] = pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp()   # 1er du mois
    return ds[ACC_VARS]

def mask_and_coarsen(ds):
    ds = ds.sortby("latitude").sortby("longitude")
    lon2d, lat2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
    mask = xr.DataArray(contains_xy(geometry, lon2d, lat2d),
                        coords={"latitude": ds.latitude, "longitude": ds.longitude},
                        dims=("latitude", "longitude"))
    return ds.where(mask).coarsen(latitude=FACTOR, longitude=FACTOR, boundary="pad").mean()

def month_start_unique(ds, name):
    """Temps ramenés au 1er du mois ; les doublons éventuels sont signalés puis retirés (on garde le dernier)."""
    ds = ds.assign_coords(time=pd.DatetimeIndex(ds.time.values).to_period("M").to_timestamp())
    idx = ds.indexes["time"]
    dup = idx.duplicated(keep="last")
    print(f"{name} : {ds.sizes['time']} pas de temps, {int(dup.sum())} doublon(s) retiré(s)")
    if dup.any():
        print("   mois concernés :", sorted(set(idx[idx.duplicated(keep=False)].strftime("%Y-%m"))))
    return ds.isel(time=~dup)

fix = xr.concat([load_byhour(p) for p in byhour_files.values()], dim="time").sortby("time")
fix = month_start_unique(fix, "by-hour")
fix = mask_and_coarsen(fix)

ds_dz = xr.open_dataset(f"{OUT_DIR}/era5land_algeria_masked_x{FACTOR}.nc").load()
if "valid_time" in ds_dz.coords and "time" not in ds_dz.coords:
    ds_dz = ds_dz.rename({"valid_time": "time"})
ds_dz = month_start_unique(ds_dz, "fichier de l'EDA")
assert np.allclose(fix.latitude, ds_dz.latitude) and np.allclose(fix.longitude, ds_dz.longitude), \
    "grilles différentes : vérifier AREA / FACTOR"

# %% 3. VALIDATION avant remplacement : sur une année saine, by-hour 00:00 doit ≈ produit mensuel
rows = []
for v in ACC_VARS:
    a = fix[v].sel(time=slice(f"{CHECK_YEAR}-01", f"{CHECK_YEAR}-12"))
    b = ds_dz[v].sel(time=a.time)
    rows.append({"var": v,
                 "ratio_moyen": float(a.mean() / b.mean()),
                 "corr_points": float(xr.corr(a, b)),
                 "ecart_rel_median_%": float(100 * (abs(a - b) / abs(b).where(abs(b) > 0)).median())})
print(pd.DataFrame(rows).round(4))
# Attendu : ratio ≈ 1 et corr ≈ 1. Si le ratio est très différent de 1 (ex. ×24, ×1000),
# les unités ne sont pas les mêmes : NE PAS remplacer avant d'avoir compris.

# %% 4. Remplacement des 7 variables sur les 18 mois affectés
ds_clean = ds_dz.copy(deep=True)
for v in ACC_VARS:
    ds_clean[v].loc[{"time": FIX_MONTHS}] = fix[v].sel(time=FIX_MONTHS).transpose(*ds_clean[v].dims).values
ds_clean.to_netcdf(f"{OUT_DIR}/era5land_algeria_masked_x{FACTOR}_corrected.nc")

# %% 5. Contrôle visuel + statistique : l'anomalie a-t-elle disparu ?
def monthly_z(ds):
    m = ds[ACC_VARS].mean(["latitude", "longitude"]).to_dataframe()
    med = m.groupby(m.index.month).transform("median")
    mad = m.groupby(m.index.month).transform(lambda x: (x - x.median()).abs().median()) * 1.4826
    return (m - med) / mad
for name, d in [("AVANT", ds_dz), ("APRÈS", ds_clean)]:
    z = monthly_z(d)
    print(name, "| nb de mois avec |z|>3 :", (z.abs() > 3).sum().to_dict())

fig, axes = plt.subplots(4, 3, figsize=(18, 12), sharex=True)
mo = ds_clean[VARS].mean(["latitude", "longitude"]).to_dataframe()
for ax, v in zip(axes.ravel(), VARS):
    mo[v].plot(ax=ax, title=v); ax.axvspan("2022-09-01", "2024-02-28", color="orange", alpha=0.15)
plt.tight_layout(); fig.savefig("figures/f20_variation_mensuelle_corrigee.png", dpi=200)

# %% 6. DataFrame, suppression des NaN, conversions
df = ds_clean[VARS].to_dataframe().reset_index().dropna()
n_valid = int((~ds_clean["t2m"].isnull().all("time")).sum())
assert len(df) == n_valid * ds_clean.sizes["time"], (len(df), n_valid * ds_clean.sizes["time"])

print("NaN restants :", int(df.isna().sum().sum()))
df["t2m"] -= 273.15; df["d2m"] -= 273.15              # Kelvin -> °C
# (les autres variables restent en unités SI ; la standardisation absorbe les échelles)

# %% 7. Valeurs aberrantes : mesures AVANT transformation
from scipy.stats import skew, kurtosis
HEAVY = ["ro", "tp", "slhf", "e"]

def outlier_report(d, cols):
    q1, q3 = d[cols].quantile(.25), d[cols].quantile(.75); iqr = q3 - q1
    pct = ((d[cols] < q1 - 1.5*iqr) | (d[cols] > q3 + 1.5*iqr)).mean() * 100
    return pd.DataFrame({"skew": skew(d[cols]), "kurtosis": kurtosis(d[cols]), "%IQR": pct}, index=cols).round(2)

# Découpage chronologique PROVISOIRE (le vrai découpage sera fait avec la construction de la cible)
train = df[df["time"] < "2024-01-01"]
print("AVANT\n", outlier_report(train, HEAVY))

# %% 8. Transformation des queues lourdes : log signé avec échelle apprise sur le train
# Pourquoi pas log1p(x) direct ? Ici |x| ~ 1e-7 à 1e-2 : log1p(x) ≈ x, donc aucun effet.
# On divise d'abord par une échelle typique s (médiane de |x| sur le train) : log1p(|x|/s).
from sklearn.base import BaseEstimator, TransformerMixin

class SignedLog1p(BaseEstimator, TransformerMixin):
    def __init__(self, cols): self.cols = cols
    def fit(self, X, y=None):
        self.scale_ = {c: (np.median(np.abs(X[c])) or np.mean(np.abs(X[c]))) for c in self.cols}
        return self
    def transform(self, X):
        X = X.copy()
        for c in self.cols:
            X[c] = np.sign(X[c]) * np.log1p(np.abs(X[c]) / self.scale_[c])   # monotone, garde le signe
        return X

slog = SignedLog1p(HEAVY).fit(train)
train_t = slog.transform(train)
print("APRÈS\n", outlier_report(train_t, HEAVY))
# Alternative du cours : Yeo-Johnson, mais APPLIQUÉE SUR x/s (sinon quasi identité aux petites échelles)
#   from sklearn.preprocessing import PowerTransformer
#   PowerTransformer("yeo-johnson").fit(train[HEAVY] / pd.Series(slog.scale_))

# %% 9. Scaling : à ajuster sur le train uniquement (après sélection des variables)
# from sklearn.preprocessing import StandardScaler, RobustScaler
# scaler = StandardScaler().fit(train_t[FEATURES]);  X_train = scaler.transform(train_t[FEATURES])