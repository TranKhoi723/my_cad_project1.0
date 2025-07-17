#!/bin/bash

# Dòng này đảm bảo script sẽ thoát ngay lập tức nếu có bất kỳ lệnh nào thất bại
set -e

# "exec" sẽ thay thế tiến trình của script này bằng lệnh được truyền vào.
# "$@" là một biến đặc biệt trong bash, đại diện cho TẤT CẢ các tham số
# được truyền vào script (ví dụ: "freecadcmd", "/app/scripts/pipeline.py").
exec "$@"