import json
from pathlib import Path

import altair as alt
import pandas as pd
import pytest

import datapane as dp
from datapane.client import api
from datapane.common.df_processor import convert_csv_pd

from ..local.test_api import gen_report_simple, gen_report_with_files
from .common import deletable, gen_df, gen_headline, gen_name

pytestmark = pytest.mark.usefixtures("dp_login")


def test_report_simple():
    report = gen_report_simple()
    report.publish(name="TEST", headline="HEADLINE")
    with deletable(report):
        ...


def test_report_with_single_file(datadir: Path):
    report = gen_report_with_files(datadir, single_file=True)
    # Test we can save then publish
    report.save(str(datadir / "test_report.html"))
    report.publish(name="TEST", headline="HEADLINE")
    with deletable(report):
        ...


def test_report_with_files(datadir: Path):
    report = gen_report_with_files(datadir)
    report.publish(name="TEST", headline="HEADLINE")
    with deletable(report):
        ...


def test_report(tmp_path: Path):
    df = gen_df()
    name = gen_name()
    headline = gen_headline()

    # create a basic report
    m = dp.Markdown("hello world!!")

    # Asset tests
    lis = [1, 2, 3]
    json_list: str = json.dumps(lis)
    plot = alt.Chart(df).mark_line().encode(x="x", y="y")

    # create the DP
    fn = tmp_path / "json_list.json"
    fn.write_text(data=json_list)
    file_asset = dp.File(file=fn)
    json_asset = dp.File(data=json_list, is_json=True)
    plot_asset = dp.Plot(data=plot)
    list_asset = dp.File(data=lis, is_json=True)
    df_asset = dp.Table(df=df, caption="Our Dataframe")
    dp_report = api.Report(m, file_asset, df_asset, json_asset, plot_asset, list_asset)
    dp_report.publish(name=name, headline=headline)

    with deletable(dp_report):
        # are the fields ok
        assert dp_report.headline == headline
        assert len(dp_report.top_block.blocks) == 6

        # NOTE - Asset objects no longer exists - thus below tests can't be supported
        # we do store `id` on the object, that can be used to pull out from the XML report
        # but currently unsupported

        # # --- FILE ASSET --- #
        # # [1, 2, 3] uploaded via a JSON file
        #
        # fn = tmpdir / "tmp1.json"
        # file_asset.download_file(fn)
        # asset1 = fn.read_text()
        # assert asset1 == json_list
        #
        # # check the file asset via download_obj
        # loaded_file = file_asset.download_obj()
        # assert loaded_file == lis
        #
        # # --- JSON ASSET --- #
        # # [1, 2, 3] uploaded as a JSON string
        #
        # # check the json asset via download_file
        # with temp_fname(".json") as fn:
        #     fn = Path(fn)
        #     json_asset.download_file(fn)
        #     assert fn.read_text() == json_list
        #
        # # check the json asset via download_obj
        # loaded_json = json_asset.download_obj()
        # assert loaded_json == lis
        #
        # # --- LIST ASSET --- #
        # # [1, 2, 3] uploaded as a native Python list
        #
        # # check the list asset via download_file
        # with temp_fname(".json") as fn:
        #     fn = Path(fn)
        #     list_asset.download_file(fn)
        #     assert fn.read_text() == json_list
        #
        # # check the list asset via download_obj
        # loaded_list = list_asset.download_obj()
        # assert loaded_list == lis
        #
        # # --- PLOT ASSET --- #
        #
        # # check the plot asset via download_file
        # with temp_fname(".json") as fn:
        #     fn = Path(fn)
        #     plot_asset.download_file(fn)
        #     assert json.loads(fn.read_text()) == plot.to_dict()
        #
        # # check the plot asset via download_obj
        # loaded_obj = plot_asset.download_obj()
        # assert loaded_obj == plot.to_dict()
        #
        # # --- DF ASSET --- #
        #
        # # check the df asset
        # df1 = df_asset.download_df()
        # check_df_equal(df1, df)


def test_complex_df_report():
    """Test our dataframe importing with types of DFs user's upload"""
    tz_df = convert_csv_pd(
        """
        date,datetime,datetime_tz
        2017-01-10,2017-01-21T23:10:24,2020-03-23T00:00:00.000Z
        2017-01-11,2017-01-23T23:01:24,2020-04-23T00:00:00.000Z
    """
    )

    raw_data = {
        "first_name": ["Jason", "Molly", "Tina", "Jake", "Amy"],
        "last_name": ["Miller", "Jacobson", "Ali", "Milner", "Cooze"],
        "age": [42, 52, 36, 24, 73],
        "preTestScore": [4, 24, 31, 2, 3],
        "postTestScore": [25, 94, 57, 62, 70],
    }
    index_df = pd.DataFrame(
        raw_data, columns=["first_name", "last_name", "age", "preTestScore", "postTestScore"]
    )
    df_desc = index_df.describe()
    df_desc_2 = df_desc.reset_index()

    tz_t = dp.Table(tz_df)
    index_t = dp.Table(index_df)
    df_desc_t = dp.Table(df_desc)
    df_desc_2_t = dp.Table(df_desc_2)

    with deletable(dp.Report(tz_t, index_t, df_desc_t, df_desc_2_t)) as dp_report:
        dp_report.publish(name=gen_name())

        # NOTE - as above, downloading embedded assets from a report currently not supported in API
        # check_df_equal(tz_df, tz_t.download_df())
        # check_df_equal(index_df, index_t.download_df())
        # check_df_equal(df_desc, df_desc_t.download_df())
        # check_df_equal(df_desc_2, df_desc_2_t.download_df())
