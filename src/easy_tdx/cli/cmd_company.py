"""通达信原生 F10 / 财务快照命令（TDX 协议，与 Web 层 ``/finance`` ``/company/*`` 同源）。

与 ``cmd_finance.py`` 的新浪三表（``f10``）区别：
  - ``f10``                走新浪 HTTP，输出多期结构化利润表/负债表/现金流
  - 本模块走通达信协议，输出最新一期财务快照 + F10 全文板块
"""

from __future__ import annotations

import click

from ..models.enums import Market
from .parsers import parse_market


@click.command("finance-info")
@click.argument("market")
@click.argument("code")
@click.option("--table", "use_table", is_flag=True, help="表格输出")
@click.option("--output", "output_fmt", type=click.Choice(["json", "table", "csv"]), default="json")
def finance_info(market: str, code: str, use_table: bool, output_fmt: str) -> None:
    """获取最新财务快照（通达信协议，30+ 项单期指标）。

    含股本结构、资产负债、利润、现金流、每股指标等最新一期数据。
    与 ``f10``（新浪多期三表）互补，本命令仅返回最新一期。

    \b
    示例：

      easy-tdx finance-info SH 600519 --table

      easy-tdx finance-info SZ 000001
    """
    from ..exceptions import TdxError
    from .conn import get_tdx_client
    from .output import print_error, print_output

    fmt = "table" if use_table else output_fmt
    mkt = Market(parse_market(market))
    try:
        with get_tdx_client() as client:
            df = client.get_finance_info(mkt, code)
    except TdxError as e:
        print_error(str(e))
        raise SystemExit(1) from e
    print_output(df, fmt)


@click.command("company-info")
@click.argument("market")
@click.argument("code")
@click.argument("name_or_filename", required=False, default=None)
@click.option("--table", "use_table", is_flag=True, help="表格输出（仅列目录时生效）")
@click.option("--output", "output_fmt", type=click.Choice(["json", "table", "csv"]), default="json")
@click.option(
    "--offset",
    default=0,
    type=int,
    help="读正文偏移（字节）：传板块名时为板块内相对偏移，传文件名时为文件绝对偏移，默认 0",
)
@click.option("--length", default=1024, type=int, help="读正文长度（字节，默认 1024）")
def company_info(
    market: str,
    code: str,
    name_or_filename: str | None,
    use_table: bool,
    output_fmt: str,
    offset: int,
    length: int,
) -> None:
    """获取 F10 公司信息：无板块名参数列目录，有板块名参数读正文。

    \b
    两种用法：

      # 1. 列出 F10 板块目录（最新提示/公司概况/财务分析/... 共 16 板块）
      easy-tdx company-info SH 600519 --table

      # 2. 读取指定板块正文（板块名自动解析定位）
      easy-tdx company-info SH 600519 "公司概况"
      easy-tdx company-info SH 600519 "分红扩股" --length 2048

    \b
    读正文时，name_or_filename 既可传板块名（如 ``最新提示``），也可直接传文件名
    （如 ``600519.txt``）。``--offset`` 语义随入参而定：传板块名时为板块内相对
    偏移（0 = 板块起点）；传文件名时为文件绝对偏移。
    """
    mkt = Market(parse_market(market))
    if name_or_filename is None:
        _run_category(mkt, code, use_table, output_fmt)
    else:
        _run_content(mkt, code, name_or_filename, offset, length)


@click.command("company-info-content", hidden=True)
@click.argument("market")
@click.argument("code")
@click.argument("name_or_filename")
@click.option(
    "--offset",
    default=0,
    type=int,
    help="偏移（字节）：传板块名时为板块内相对偏移，传文件名时为文件绝对偏移，默认 0",
)
@click.option("--length", default=1024, type=int, help="读取长度（字节，默认 1024）")
def company_info_content(
    market: str, code: str, name_or_filename: str, offset: int, length: int
) -> None:
    """[已弃用，改用 company-info] 读取 F10 公司信息板块正文。

    此命令为向后兼容保留（隐藏，不出现在 --help）。新用法::

        easy-tdx company-info SH 600519 "公司概况"
    """
    mkt = Market(parse_market(market))
    _run_content(mkt, code, name_or_filename, offset, length)


# --------------------------------------------------------------------------- #
# 内部实现：列目录 / 读正文
# --------------------------------------------------------------------------- #


def _run_category(market: Market, code: str, use_table: bool, output_fmt: str) -> None:
    """列出 F10 板块目录并输出。"""
    from ..exceptions import TdxError
    from .conn import get_tdx_client
    from .output import print_error, print_output

    fmt = "table" if use_table else output_fmt
    try:
        with get_tdx_client() as client:
            df = client.get_company_info_category(market, code)
    except TdxError as e:
        print_error(str(e))
        raise SystemExit(1) from e
    print_output(df, fmt)


def _run_content(
    market: Market, code: str, name_or_filename: str, offset: int, length: int
) -> None:
    """读取 F10 板块正文并输出。"""
    from ..exceptions import TdxError
    from .conn import get_tdx_client
    from .output import print_error

    try:
        with get_tdx_client() as client:
            filename, seg_start, matched_board = _resolve_filename(
                client, market, code, name_or_filename
            )
            # 板块名命中：--offset 解释为板块内相对偏移（默认 0 = 板块起点）
            # 文件名：--offset 解释为文件绝对偏移
            effective_offset = seg_start + offset if matched_board else offset
            content = client.get_company_info_content(
                market, code, filename, effective_offset, length
            )
    except _ResolveError as e:
        print_error(str(e))
        raise SystemExit(1) from e
    except TdxError as e:
        print_error(str(e))
        raise SystemExit(1) from e
    click.echo(content)


class _ResolveError(Exception):
    """板块名解析失败（内部信号异常，与 TdxError 分开捕获）。"""


def _resolve_filename(
    client: object, market: Market, code: str, name_or_filename: str
) -> tuple[str, int, bool]:
    """把板块名或文件名解析为 (filename, 板块起始 offset, 是否板块名命中)。

    策略：先查 F10 目录，若 ``name_or_filename`` 命中某个板块名则返回
    (对应 filename, 该板块 start, True)；否则视为文件名返回 (name_or_filename, 0, False)。
    返回的 ``matched`` 决定 ``--offset`` 的语义：板块名时为相对偏移，文件名时为绝对偏移。
    """
    # 形如 '600519.txt' 的文件名，跳过目录查询直接用（offset 为绝对偏移）
    if "." in name_or_filename:
        return name_or_filename, 0, False

    df = client.get_company_info_category(market, code)  # type: ignore[attr-defined]
    if not df.empty:
        row = df.loc[df["name"] == name_or_filename]
        if not row.empty:
            return str(row["filename"].iloc[0]), int(row["start"].iloc[0]), True

    # 未命中板块名：当作不带后缀的纯 ASCII 文件名兜底（如 '600519' → '600519.txt'）
    if name_or_filename.isascii() and name_or_filename.isalnum():
        return f"{name_or_filename}.txt", 0, False

    available = "" if df.empty else "、".join(df["name"].tolist())
    raise _ResolveError(
        f"未找到板块名 '{name_or_filename}'。"
        + (f"可用板块：{available}" if available else "请先运行 `easy-tdx company-info` 查看目录。")
    )
