# 生成数据说明 Quickstart

## 数据初筛（合成工程文件）

`数据初筛_Win10.bat` 是独立脚本。将它复制到目标的集（场）目录（例如
`TLP\002` 或 `LDX\Production\scenes\999`）后双击运行，即会在同一目录生成：

```text
TLP_002_DataFilter.txt
```

文件逐行记录每个有效镜头的 `cmp/task` 目录中版本号最高的工程文件名。脚本
会跳过 `.autosave`、备份文件与 `~$` Office 临时文件；运行环境需要 Python 3。
项目代码会从当前集（场）目录向上查找最近的三位大写目录名，因此支持中间包含
`Production\scenes` 等目录层级的项目结构。

`生成数据说明_Win10.bat` 是一个 Windows 10 可直接双击运行的脚本。将它放到 `Train_Data` 根目录后，会自动扫描该目录下的数据组子目录，并在每个有效数据组中生成对应的 `.xlsx` 数据说明文件。

## 1. 准备目录

数据根目录示例：

```text
Train_Data/
  生成数据说明_Win10.bat
  XHTVC_C01/
    01_shots/
      XHTVC_C01_io_v001.mov
      XHTVC_C01_cmp_v001.mov
    02_assets/
      XHTVC_C01_lgt_v001.mov
  LDX_019_006019/
    01_shots/
    02_assets/
```

脚本只处理同时包含以下两个子目录的数据组：

```text
01_shots
02_assets
```

如果数据组里的 `01_shots` 是空的，脚本会跳过该数据组，不会报错。

## 2. 拷贝脚本

只需要拷贝这一个文件：

```text
生成数据说明_Win10.bat
```

将它放到目标项目的数据根目录，例如：

```text
Z:\Project\LDX\Train_Data\生成数据说明_Win10.bat
```

不需要额外拷贝 `steps_activation.py` 或 `requirements.txt`，因为 Python 逻辑已经内嵌在 bat 文件里。

## 3. 运行脚本

双击 `生成数据说明_Win10.bat`。

运行时脚本会自动：

1. 以 bat 所在目录作为 `Train_Data` 根目录。
2. 检查本机是否安装 Python 3。
3. 检查依赖：`opencv-python`、`openpyxl`、`Pillow`。
4. 如果依赖缺失，会自动通过 `pip install` 安装。
5. 扫描所有有效数据组。
6. 规范化文件名前缀。
7. 在每个数据组目录下生成 `.xlsx` 数据说明文件。

运行结束后，窗口会显示：

```text
Done. Excel files have been generated in each data group folder.
Press any key to continue . . .
```

此时所有处理已经完成。按任意键后，cmd 窗口会关闭。

## 4. 输出结果

每个有效数据组会生成一个同名数据说明文件：

```text
Train_Data/
  XHTVC_C01/
    XHTVC_C01_数据说明.xlsx
```

如果同名 `.xlsx` 已经存在，脚本会覆盖它。

如果该 Excel 文件正在被 Excel/WPS 打开，脚本会写入失败。请关闭文件后重新运行。

## 5. 文件重命名规则

`01_shots` 下的过程文件会按排序结果添加或修正 `F` 前缀：

```text
F001_xxx.mov
F002_xxx.mov
F003_xxx.mov
```

`02_assets` 下的素材文件会按排序结果添加或修正 `A` 前缀：

```text
A001_xxx.mov
A002_xxx.png
```

如果文件已经带有正确的 `F001_` / `A001_` 前缀，脚本会跳过，不重复重命名。

如果文件带有前缀但顺序不正确，脚本会按当前排序重新编号。

如果目标文件名已经存在且会造成冲突，脚本会停止并报错，不会覆盖已有媒体文件。

## 6. 常见提示

### Python was not found

本机没有可用的 Python。请安装 Python 3，并勾选 `Add Python to PATH`。

### Installing dependencies, please wait...

首次运行时依赖缺失，脚本正在自动安装。需要网络可访问 pip 源。

### 跳过空数据组

表示该数据组有 `01_shots` / `02_assets` 结构，但 `01_shots` 里没有文件。脚本会继续处理其他数据组。

### 没有非空数据组，未生成 Excel。

表示当前 `Train_Data` 下没有可生成数据说明的非空数据组。

### Failed. Please check the error message above.

表示本轮运行失败。通常需要查看上方具体错误，例如 Excel 文件被打开、依赖安装失败、文件名冲突等。
