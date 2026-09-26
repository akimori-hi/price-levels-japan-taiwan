"""reverse Balassa-Samuelson回帰（Penn effect：log(relp) ~ log(reli)）のユーティリティ。

単回帰・トリム回帰に加え、以下を含む。
- 国クラスタロバストSE・国×年の二方向クラスタロバストSE
- 年別の横断面回帰（プール回帰による「収束」解釈を年ごとに直接確認するため）
- 年固定効果付きプール回帰
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def ols(x: np.ndarray, y: np.ndarray):
    """単回帰。係数(b)・残差(r)・決定係数(R2)を返す。"""
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    r2 = 1 - (r ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, r, r2


def trim_ols(x: np.ndarray, y: np.ndarray, k: float = 2.5, iters: int = 4):
    """外れ値を反復的に除外したロバスト回帰（k×残差標準偏差を超える点を除く）。"""
    keep = np.ones(len(x), dtype=bool)
    for _ in range(iters):
        b, r, _ = ols(x[keep], y[keep])
        new_keep = np.abs(y - (b[0] + b[1] * x)) <= k * r.std()
        if new_keep.sum() == keep.sum():
            break
        keep = new_keep
    b, _, _ = ols(x[keep], y[keep])
    return b, y - (b[0] + b[1] * x), keep


def hc3_se(x: np.ndarray, y: np.ndarray) -> float:
    """傾き係数のHC3（不均一分散頑健）標準誤差。"""
    X = np.column_stack([np.ones_like(x), x])
    n = len(x)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    inv = np.linalg.inv(X.T @ X)
    h = np.diag(X @ inv @ X.T)
    u = e / (1 - h)
    cov = inv @ (X.T @ np.diag(u ** 2) @ X) @ inv
    return float(np.sqrt(np.diag(cov))[1])


def classical_se(x: np.ndarray, y: np.ndarray) -> float:
    """傾き係数の古典的（均一分散仮定）標準誤差。"""
    X = np.column_stack([np.ones_like(x), x])
    n = len(x)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    inv = np.linalg.inv(X.T @ X)
    sigma2 = (e ** 2).sum() / (n - 2)
    return float(np.sqrt(np.diag(sigma2 * inv))[1])


def cluster_se(df: pd.DataFrame, cluster_col: str, x_col: str = "log_x", y_col: str = "log_y") -> float:
    """傾き係数の国クラスタロバストSE（statsmodels経由）。"""
    result = smf.ols(f"{y_col} ~ {x_col}", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df[cluster_col]}
    )
    return float(result.bse[x_col])


def twoway_cluster_se(df: pd.DataFrame, cluster_col1: str, cluster_col2: str,
                       x_col: str = "log_x", y_col: str = "log_y") -> float:
    """傾き係数の二方向（国×年）クラスタロバストSE。

    statsmodelsの二方向クラスタ実装はグループ配列を構造化dtypeに変換するため、
    文字列の国コードをそのまま渡すとエラーになる。整数コードに変換してから渡す。
    """
    d = df.copy()
    d["_cluster1_code"] = pd.factorize(d[cluster_col1])[0]
    d["_cluster2_code"] = pd.factorize(d[cluster_col2])[0]
    result = smf.ols(f"{y_col} ~ {x_col}", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d[["_cluster1_code", "_cluster2_code"]].to_numpy()}
    )
    return float(result.bse[x_col])


def fit_penn_regression_by_year(df: pd.DataFrame, x_col: str = "reli", y_col: str = "relp",
                                 year_col: str = "year") -> pd.DataFrame:
    """年ごとに横断面回帰を独立に行い、各年の傾き・残差を求める。

    プール回帰（全期間を1つの傾きで要約する）とは異なり、年ごとの傾き自体の変化も
    観察できる。残差はその年の横断面回帰から得られたものなので、年をまたいだ
    「収束」の解釈は、この年別残差を直接比較して行う。
    """
    rows = []
    for year, group in df.groupby(year_col):
        fit = fit_penn_regression(group, x_col=x_col, y_col=y_col)
        fit["fit_year"] = year
        fit["fit_slope"] = fit.attrs["slope"]
        fit["fit_r_squared"] = fit.attrs["r_squared"]
        rows.append(fit)
    return pd.concat(rows, ignore_index=True)


def fit_penn_regression_with_year_fe(df: pd.DataFrame, x_col: str = "reli", y_col: str = "relp",
                                      country_col: str = "countrycode", year_col: str = "year"):
    """年固定効果付きのプール回帰（国クラスタロバストSE）。

    年ごとに共通する変動（世界的な物価・所得のショック等）を年ダミーで吸収した上で、
    所得と物価水準の関係を推定する。残差は「その年の世界共通要因を除いた上での、
    所得水準から予想される物価水準からのズレ」を表す。
    """
    d = df.copy()
    d["log_x"] = np.log(d[x_col])
    d["log_y"] = np.log(d[y_col])
    model = smf.ols(f"log_y ~ log_x + C({year_col})", data=d)
    result = model.fit(cov_type="cluster", cov_kwds={"groups": d[country_col]})
    d["fitted"] = result.fittedvalues
    d["resid"] = result.resid
    d["resid_pct"] = (np.exp(d["resid"]) - 1) * 100
    return d, result


def fit_penn_regression(df: pd.DataFrame, x_col: str = "reli", y_col: str = "relp") -> pd.DataFrame:
    """log-logのPenn回帰を実行し、残差付きのデータフレームを返す。"""
    d = df.copy()
    x = np.log(d[x_col].to_numpy())
    y = np.log(d[y_col].to_numpy())
    b, r, r2 = ols(x, y)
    d["log_x"] = x
    d["log_y"] = y
    d["fitted"] = b[0] + b[1] * x
    d["resid"] = r
    d["resid_pct"] = (np.exp(r) - 1) * 100
    d.attrs["intercept"] = b[0]
    d.attrs["slope"] = b[1]
    d.attrs["r_squared"] = r2
    return d
