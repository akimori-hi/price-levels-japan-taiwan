# 所得で条件づけた物価水準の国際比較──日本・台湾のケース：分析コード

秋森弘「所得で条件づけた物価水準の国際比較──日本・台湾のケース」（『北星論集』、2026年投稿）の
分析コードと、そこから得られた処理済みデータ・集計表です。論文中の数値は、すべてこのリポジトリの
実行済みノートブックから転記しています。

Replication code for "Income-Conditioned Price Levels across Countries: The Cases of Japan and
Taiwan" (in Japanese, *Hokusei Review*, submitted 2026). All figures in the paper are
transcribed from the executed notebooks in this repository.

## 内容

Penn World Table 11.0を用いて、高所得国（一人当たりGDP3万ドル以上、事前の除外リスト適用後）の
家計消費のドル建て物価水準を一人当たり所得に回帰し（Penn effect）、所得から予測される物価水準と
実際の物価水準との差（残差）を日本・台湾・韓国について求めます。

| ノートブック | 内容 |
|---|---|
| `01_pwt_data_acquisition` | Penn World Table 11.0の取得、各年の米国＝1.00の相対物価水準・相対所得の作成 |
| `02_ppp_deviation_panel` | 高所得クラブの定義（除外リストを含む）、2005〜2023年のパネルと2023年の横断面 |
| `03_reverse_bs_regression` | 2023年横断面回帰、標準誤差（HC3・国クラスタ・二方向クラスタ）、年固定効果、年別回帰、トリム回帰、所得閾値・所得指標・除外リストの感度分析 |
| `04_taiwan_deep_dive` | 台湾の工業部門の労働生産性指数と残差の関係 |
| `05_japan_taiwan_residual` | 日本・台湾の残差の年別比較と、他の指標との比較 |
| `06_figures_hokusei` | 論文の図1・図2（英語ラベル・日本語ラベル） |
| `07_outlier_and_benchmark_year` | 台湾の外れ値の評価（外部スチューデント化残差、Cook's D、台湾を除く回帰の95%予測区間）、ICP基準年（2021年）での確認 |

`src/` は回帰と台湾データ整形の関数、`data/processed/` は処理済みデータ、`output/tables/` は
集計表、`output/figures/` は図です。

## 再現方法

1. Python 3.12で動作を確認しています。`pip install -r requirements.txt`
2. 生データを`data/raw/`に置きます（再配布はしていません）。
   - **Penn World Table 11.0**：`01`は`data/raw/pwt110_raw.xlsx`がなければDataverseNLから自動で取得します。
     取得できない場合は、DOI [10.34894/FABVLR](https://doi.org/10.34894/FABVLR) のページから
     `pwt110.xlsx`を入手し、`data/raw/pwt110_raw.xlsx`として保存してください。
   - **台湾の労働生産性指数**：台湾行政院主計總處「薪情平臺」（<https://earnings.dgbas.gov.tw/>）から
     「勞動生產力指數(產量)」（工業・服務業、月次）をExcel形式で出力し、
     `data/raw/taiwan_labor_productivity_raw.xlsx`として保存してください（`04`で使用）。
3. `notebooks/`のノートブックを`01`から`07`の順に実行します。
   例：`jupyter nbconvert --to notebook --execute --inplace notebooks/01_pwt_data_acquisition.ipynb`

## データの出所

- Groningen Growth and Development Centre (2025). Penn World Table version 11.0 [Data set]. DataverseNL. <https://doi.org/10.34894/FABVLR>
  （Feenstra, R. C., Inklaar, R., and Timmer, M. P. (2015). The next generation of the Penn World Table. *American Economic Review*, 105(10), 3150–3182.）
- 台湾行政院主計總處「薪情平臺」勞動生產力指數（產量） <https://earnings.dgbas.gov.tw/>

## ライセンス

コードはMIT Licenseです（`LICENSE`）。データの利用条件は、それぞれの提供元に従ってください。
