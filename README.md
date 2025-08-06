My CAD Project: Giải pháp tự động hóa bản vẽ kỹ thuật đỉnh cao
My CAD Project là một hệ thống tự động hóa tiên tiến, được thiết kế để biến các mô hình 3D định dạng STEP thành những bản vẽ kỹ thuật 2D chuyên nghiệp và chất lượng cao. Dự án này kết hợp sức mạnh của các công cụ CAD mã nguồn mở như FreeCAD và ezdxf vào một quy trình làm việc liền mạch, được đóng gói hoàn chỉnh bằng Docker để đảm bảo tính nhất quán và khả năng tái tạo vượt trội trên mọi môi trường.

🚀 Tại sao lại là My CAD Project?
Chúng tôi không chỉ dừng lại ở việc chuyển đổi 3D sang 2D đơn thuần. My CAD Project mang đến một cấp độ tự động hóa và chi tiết mới, giúp bạn tạo ra các bản vẽ kỹ thuật đạt chuẩn công nghiệp một cách dễ dàng và hiệu quả.

✨ Những tính năng nổi bật
Quy trình tự động hóa hoàn chỉnh: Từ khi nhập mô hình 3D STEP đến khi xuất ra bản vẽ 2D cuối cùng, mọi bước đều được tự động hóa, giảm thiểu tối đa sự can thiệp thủ công và nguy cơ sai sót.

Bố cục bản vẽ thông minh: Hệ thống tự động sắp xếp các hình chiếu chính (mặt trước, mặt trên, mặt bên) và hình chiếu đẳng cấp (Isometric) một cách tối ưu trên khổ giấy đã chọn, đảm bảo bản vẽ luôn gọn gàng và chuyên nghiệp.

Kích thước tự động thông minh: Không còn phải đặt kích thước thủ công! Dự án này tự động phân tích hình học của mô hình để áp dụng các loại kích thước cần thiết như tuyến tính, bán kính, đường kính và góc.

Hiển thị nâng cao: Các đường ẩn được tự động tính toán và hiển thị rõ ràng, cùng với việc tạo đường tâm cho các tính năng tròn (lỗ, trụ), giúp bản vẽ dễ đọc và cung cấp đầy đủ thông tin.

Tỷ lệ linh hoạt: Hệ thống có khả năng tự động tính toán tỷ lệ bản vẽ tối ưu dựa trên kích thước của chi tiết và khổ giấy. Bạn cũng có thể dễ dàng đặt tỷ lệ thủ công nếu muốn kiểm soát tuyệt đối.

Đầu ra tiêu chuẩn ngành: Bản vẽ cuối cùng được xuất ra ở định dạng DXF (phù hợp để chỉnh sửa trong các phần mềm CAD chuyên nghiệp) và SVG (lý tưởng để xem trên web hoặc tích hợp vào tài liệu).

Cấu hình tương tác: Script run.sh cung cấp một giao diện dòng lệnh thân thiện, cho phép bạn dễ dàng chọn tệp STEP đầu vào, template bản vẽ và cấu hình các thông số chi tiết cho quá trình tạo bản vẽ.

💡 Vượt trội hơn các công cụ chuyển đổi CAD cơ bản
Trong khi nhiều công cụ chỉ đơn thuần chuyển đổi 3D sang 2D, My CAD Project nổi bật với khả năng cung cấp một giải pháp toàn diện và thông minh:

Tự động hóa toàn diện: Không chỉ là một công cụ, đây là một quy trình làm việc hoàn chỉnh được điều phối bởi pipeline.py, giúp bạn tiết kiệm thời gian và công sức đáng kể.

Tính năng bản vẽ chuyên sâu: Chúng tôi đi xa hơn việc chỉ tạo hình chiếu. My CAD Project tập trung vào việc tạo ra các bản vẽ kỹ thuật thực sự, bao gồm các chi tiết quan trọng như kích thước tự động, đường ẩn và đường tâm, biến dữ liệu 3D thành thông tin kỹ thuật hữu ích.

Quản lý môi trường mạnh mẽ: Nhờ Docker, mọi phụ thuộc đều được đóng gói gọn gàng, loại bỏ các vấn đề tương thích và đảm bảo kết quả nhất quán mọi lúc, mọi nơi.

Cấu hình linh hoạt: Với nhiều tùy chọn cấu hình, bạn có thể tinh chỉnh quy trình để đáp ứng các yêu cầu cụ thể của dự án, từ tiêu chuẩn bản vẽ đến chi tiết kích thước.

🛠️ Yêu cầu hệ thống
Để chạy My CAD Project, bạn chỉ cần:

Docker: Để xây dựng và quản lý môi trường chạy ứng dụng.

Git: Để sao chép mã nguồn từ repository.

🚀 Thiết lập & Chạy
Sao chép Repository:

git clone https://github.com/TranKhoi723/my_cad_project1.5.git # Hoặc URL thực tế của repository của bạn
cd my_cad_project

Khởi chạy Quy trình:
Sử dụng script run.sh để bắt đầu. Script này sẽ hướng dẫn bạn chọn tệp STEP, template SVG và cấu hình các thông số bản vẽ. Nó cũng sẽ tự động xây dựng Docker image (nếu cần) và chạy toàn bộ quy trình.

./scripts/run.sh

Lưu ý: run.sh sẽ tạo một tệp config.tmp.json tạm thời chứa các cài đặt cấu hình của bạn. Tệp này sẽ được sử dụng bởi các script Python bên trong Docker container.

⚙️ Các thông số cấu hình chính (qua run.sh)
Khi chạy run.sh, bạn sẽ được yêu cầu nhập các thông số sau để tùy chỉnh bản vẽ:

INPUT_FILE: Tên tệp STEP 3D đầu vào.

TEMPLATE_FILE: Tên tệp template SVG cho bản vẽ cuối cùng.

PROJECTION_METHOD: Phương pháp chiếu (ví dụ: THIRD_ANGLE, FIRST_ANGLE).

DRAWING_STANDARD: Tiêu chuẩn bản vẽ (ví dụ: ISO, ANSI).

SPACING_FACTOR: Hệ số giãn cách giữa các hình chiếu.

MIN_SPACING: Khoảng cách tối thiểu giữa các hình chiếu (mm).

DIMENSION_OFFSET: Khoảng cách offset của đường kích thước từ đối tượng (mm).

DIMENSION_TEXT_HEIGHT: Chiều cao văn bản kích thước (mm).

MIN_DIMENSION_LENGTH: Chiều dài tối thiểu của một cạnh để tự động thêm kích thước (mm).

MAX_DIMENSIONS_PER_VIEW: Số lượng kích thước tối đa được thêm vào mỗi hình chiếu.

DIMENSION_ANGLES: true để tự động thêm kích thước góc.

DIMENSION_RADII: true để tự động thêm kích thước bán kính.

DIMENSION_DIAMETERS: true để tự động thêm kích thước đường kính.
