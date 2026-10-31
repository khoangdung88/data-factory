# Hướng dẫn sử dụng

Bản dịch tiếng Việt của [`user-guide.md`](user-guide.md) (bản tiếng Anh là bản gốc). Tài liệu này hướng
dẫn cài đặt data-factory, tạo một gói dữ liệu, đọc kết quả và xử lý các lỗi thường gặp. Chi tiết bên
trong hệ thống xem [`technical-guide.md`](technical-guide.md).

## 1. Cài đặt

Yêu cầu: Linux/macOS/WSL, Git, [uv](https://docs.astral.sh/uv/) (uv tự cài Python 3.11).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # chỉ cần một lần, nếu chưa có uv
git clone https://github.com/khoangdung88/data-factory.git && cd data-factory
make install                                       # cài thư viện + git hooks
uv run datafactory version                         # kiểm tra đã chạy được
```

## 2. Tạo gói dữ liệu bằng một lệnh

```bash
uv run datafactory run wb-macro-indicators
```

```text
batch: c6b9e89f34fa
package: data/products/wb-macro-indicators/1.0.0
published: data/exports/wb-macro-indicators-1.0.0
```

Lệnh này gọi API của World Bank (cần internet, mất khoảng 10 giây), làm sạch và kiểm tra dữ liệu, rồi
ghi ra một gói sẵn sàng để bán. `sample-csv` là dataset mẫu chạy offline:
`uv run datafactory run sample-csv`.

## 3. Tham khảo lệnh CLI

`datafactory run <slug> [OPTIONS]`, trong đó `<slug>` là tên một thư mục trong `datasets/`.

| Tuỳ chọn | Ý nghĩa |
|---|---|
| *(không có)* | Chạy đủ collect → process → publish |
| `--stage collect` | Chỉ tải dữ liệu từ nguồn về `data/raw/` |
| `--stage process` | Chỉ làm sạch, kiểm tra một raw batch và ghi vào `data/staged/` |
| `--stage publish` | Chỉ đóng gói một batch đã xử lý vào `data/products/` và chạy các publisher |
| `--batch <id>` | Batch cần xử lý/đóng gói (mặc định: raw batch mới nhất) |
| `--release` | Chạy cả các publisher từ xa (marketplace). Không có cờ này thì không gì rời khỏi máy |

Mã thoát `0` là thành công, `1` là lỗi đã biết (thông báo in ra dạng `error: ...`).

Cấu hình (biến môi trường hoặc file `.env` ở thư mục gốc repo):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `DF_DATA_DIR` | `data` | Thư mục gốc của các vùng dữ liệu |
| `DF_DATASETS_DIR` | `datasets` | Nơi chứa định nghĩa các dataset |

## 4. Giao diện web

```bash
uv run datafactory ui            # mở http://127.0.0.1:8000
uv run datafactory ui --port 9000
```

| Trang | Việc có thể làm |
|---|---|
| **Datasets** (`/`) | Xem mọi dataset với version, batch mới nhất và gói mới nhất; `dataset.yaml` bị lỗi sẽ hiện thông báo lỗi |
| **Dataset** | Chạy pipeline (cả quy trình hoặc một bước, chọn batch, tick *release*); xem danh sách gói (tải zip), batch và schema |
| **Run** | Trạng thái, log và kết quả của một lần chạy; trang tự làm mới mỗi 2 giây đến khi xong. Mỗi dataset chỉ chạy một lần tại một thời điểm |
| **Batch** | File thô kèm checksum, số liệu chất lượng, 50 dòng hợp lệ và 50 dòng bị loại đầu tiên |
| **Product** | License, nguồn, lineage, chất lượng, danh sách file, xem trước dữ liệu, nút *Download zip* |

UI không có đăng nhập và chỉ lắng nghe trên `127.0.0.1`: không mở ra internet. Lịch sử chạy chỉ giữ trong
bộ nhớ và mất khi tắt UI; dữ liệu trong các vùng `data/` không bị ảnh hưởng.

## 5. Kết quả nhận được

```text
data/
├── raw/<slug>/<batch_id>/        file nguồn đúng như khi tải về + _manifest.json
├── staged/<slug>/<batch_id>/     data.csv (dòng hợp lệ), quarantine.csv (dòng bị loại + _error), _manifest.json
├── products/<slug>/<version>/    gói sản phẩm (không bao giờ thay đổi sau khi ghi)
└── exports/<slug>-<version>/     bản sao do publisher local_folder tạo ra
```

Thư mục gói sản phẩm là thứ anh tải lên hoặc bán:

| File | Nội dung |
|---|---|
| `data.csv` | Bảng đã làm sạch, UTF-8, có dòng tiêu đề, các cột theo schema |
| `datapackage.json` | [Frictionless Data Package](https://specs.frictionlessdata.io/data-package/): tiêu đề, version, license, nguồn, schema, sha256, số dòng, lineage, chất lượng |
| `README.md` | Datasheet cho người mua (chép từ `datasets/<slug>/README.md`) |
| `LICENSE` | Tên và URL của license |

Kiểm tra chất lượng trước khi bán: mục `quality` trong `datapackage.json` (`rows_in`, `rows_valid`,
`rows_invalid`, `null_counts`) và các dòng trong `staged/<slug>/<batch_id>/quarantine.csv`.

## 6. Các hành vi có thể tin cậy

- **Chạy lại an toàn.** Dữ liệu nguồn không đổi → cùng `batch_id`, không tạo bản trùng. Cùng dữ liệu và
  cùng version → dùng lại gói đã có.
- **Gói sản phẩm không sửa được.** Nếu dữ liệu nguồn thay đổi mà `version` giữ nguyên, bước publish dừng
  với lỗi `exists with different data; bump version`. Tăng `version` trong `dataset.yaml` (ví dụ
  `1.0.0` → `1.1.0`) rồi chạy lại.
- **Ngưỡng chất lượng chặn gói kém.** Quá ít dòng hợp lệ hoặc quá nhiều dòng bị loại → lỗi
  `valid rows < min_rows` hoặc `invalid ratio ... > max`, không gói nào được xuất bản.
- `data/` không được đưa lên Git: gói sản phẩm nằm trên máy anh cho tới khi một publisher gửi đi.

## 7. Tạo dataset của riêng anh

1. Tạo thư mục `datasets/<slug>/` (`<slug>` gồm các từ viết thường nối bằng `-`).
2. `dataset.yaml`:

```yaml
slug: my-dataset
title: Tiêu đề dễ đọc
description: Một đoạn mô tả cho người mua.
version: 1.0.0                     # tăng mỗi lần xuất bản dữ liệu hoặc schema mới
schema_version: 1                  # -> schema/v1.json
license: {name: CC-BY-4.0, path: https://creativecommons.org/licenses/by/4.0/}
source:
  plugin: local_file               # connector, xem bảng bên dưới
  license: Điều khoản cho phép chúng ta dùng và bán lại nguồn này
  params: {path: input/my.csv}     # tương đối so với thư mục dataset
reader: {plugin: csv}              # không bắt buộc, mặc định csv
processing:                        # không bắt buộc, chạy theo thứ tự
  - plugin: select_columns
    params: {columns: [id, name, price]}
quality: {min_rows: 1, max_invalid_ratio: 0.0}
publish:
  - plugin: local_folder
pricing: {model: undecided}        # tự do, chỉ để tham khảo
```

3. `schema/v1.json` — các cột của bảng cuối cùng:

```json
{"fields": [
  {"name": "id", "type": "integer", "description": "Row id", "constraints": {"required": true}},
  {"name": "name", "type": "string", "description": "Name"},
  {"name": "price", "type": "number", "description": "Price in USD"}
]}
```

Kiểu dữ liệu: `string`, `integer`, `number`, `boolean` (`true/false/1/0`), `date` (`YYYY-MM-DD`). Giá trị
rỗng là null. Cột `required` bị null hoặc sai kiểu thì dòng đó bị chuyển vào quarantine.

4. `README.md` — datasheet: bảng mô tả cột, phạm vi dữ liệu, tần suất cập nhật, nguồn và license, hạn chế.
   Thiếu file này thì không đóng gói được.
5. `uv run datafactory run <slug>`. Muốn đưa dataset vào repo thì thêm golden fixture (xem tài liệu kỹ
   thuật) và mở PR.

### Các plugin hiện có

| Tầng | Plugin | Tham số |
|---|---|---|
| connector | `local_file` | `path` |
| connector | `worldbank` | `indicators` (danh sách), `date` (`2000:2025`), `countries` (`economies` \| `all` \| `VNM;USA`), `per_page` |
| reader | `csv` | — (batch phải có đúng một file `.csv`) |
| reader | `json_records` | `pattern` (glob, mặc định `*.json`), `records_path` (danh sách key/chỉ số dẫn tới mảng bản ghi) |
| processor | `select_columns` | `columns` |
| processor | `rename_columns` | `mapping` (`tên_cũ: tên_mới`) |
| processor | `drop_rows_missing` | `columns` (bỏ dòng có bất kỳ cột nào rỗng) |
| processor | `sort_rows` | `by` |
| publisher | `local_folder` | `target_dir` (mặc định `exports`, tương đối so với `DF_DATA_DIR`) |

## 8. Xử lý lỗi

| Thông báo | Nguyên nhân → cách xử lý |
|---|---|
| `dataset 'x' not found` | Không có `datasets/x/dataset.yaml`; kiểm tra slug hoặc `DF_DATASETS_DIR` |
| `invalid dataset 'x': ...` | `dataset.yaml` thiếu trường, sai chính tả hoặc sai kiểu; đọc chi tiết trong thông báo |
| `unknown connector/processor/reader 'x'` | Gõ sai tên plugin; xem bảng ở trên |
| `no raw batch for 'x'; run the collect stage first` | Chạy không kèm `--stage` hoặc với `--stage collect` |
| `batch ... is not processed yet` | Chạy `--stage process` cho batch đó trước |
| `valid rows < min_rows` / `invalid ratio ... > max` | Xem `quarantine.csv`; sửa nguồn/bước xử lý, hoặc chủ động điều chỉnh `quality` |
| `exists with different data; bump version` | Dữ liệu của một version đã có bị thay đổi; tăng `version` |
| `datasheet README.md is required` | Thêm `datasets/<slug>/README.md` |
| `worldbank: GET ... failed` | Lỗi mạng/API; đã thử lại 3 lần; chạy lại sau |
