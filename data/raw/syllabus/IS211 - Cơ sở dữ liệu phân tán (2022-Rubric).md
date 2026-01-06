# IS211 -- CƠ SỞ DỮ LIỆU PHÂN TÁN



## THÔNG TIN CHUNG

| Tên môn học (tiếng Việt): | **Cơ sở dữ liệu phân tán** |
| --- | --- |
| Tên môn học (tiếng Anh): | **Distributed Databases** |
| Mã môn học: | IS211 |
| Thuộc khối kiến thức: | Chuyên ngành |
| Khoa/Bộ môn phụ trách: | Hệ thống thông tin |
| Giảng viên biên soạn: | ThS. Thái Bảo Trân, ThS. Nguyễn Hồ Duy Tri Email: [<trantb@uit.edu.vn>, tringuyen@uit.edu.vn]{.underline} |
| Số tín chỉ: | 4 |
| Lý thuyết: | 3 |
| Thực hành: | 1 |
| Môn học trước: | Cơ sở dữ liệu, Nhập môn mạng máy tính |


## MÔ TẢ MÔN HỌC

Sinh viên được trang bị các kiến thức về nguyên lý thiết kế cơ sở dữ liệu phân tán, quản lý giao tác, điều khiển tương tranh và phục hồi dữ liệu\... Trên cơ sở này, người học có thể nắm vững phương pháp thiết kế cơ sở dữ liệu phân tán, giải quyết được vấn đề về quản lý giao dịch, đặc trưng và các tính chất giao dịch. Cũng như, hiểu được các thuật toán điều khiển tương tranh, phục hồi dữ liệu nhằm ứng dụng vào thực tế và nghiên cứu. Đồng thời vận dụng được kỹ thuật xử lý phân tán và cách triển khai CSDL phân tán bằng Oracle/MS SQL Server.

## MỤC TIÊU MÔN HỌC (Course Goals)

Bảng 1

| ## Mục tiêu | ## Mục tiêu môn học | ## Chuẩn đầu ra trong CTĐT |
| --- | --- | --- |
| **G1** | \- Mô tả được các khái niệm cơ bản về CSDL phân tán \- Hiểu rõ các kiến trúc của hệ quản trị CSDL phân tán. | LO2 (2.7) |
| **G2** | \- Kỹ năng về thu thập các thông tin cho bài toán phân mảnh, phân tích và thiết kế được kiến trúc phân mảnh dữ liệu. \- Kỹ năng thiết kế định vị các hệ cơ sở dữ liệu phân tán vào bài toán thực tế. \- Kỹ năng xử lý dữ liệu ứng với các mức trong suốt khác nhau. \- Kỹ năng tối ưu hóa câu truy vấn trong môi trường phân tán. \- Kỹ năng về quản lý giao dịch và điều khiển đồng thời phân tán, vấn đề tương tranh và hiệu năng xử lý phân tán. | LO4 (4.1, 4.2) |
| **G3** | -Vận dụng kỹ năng hình thành ý tưởng, thiết kế và xây dựng hệ thống để giải quyết một bài toán cụ thể trong môi trường phân tán. \- Vận dụng được kỹ thuật xử lý phân tán và cách triển khai CSDL phân tán bằng Oracle/SQL Server. | LO4 (4.1, 4.2) |
| **G4** | -Vận dụng kỹ năng làm việc nhóm | LO5 (5.1, 5.2, 5.3, 5.4, 5.5, 5.6) |


## CHUẨN ĐẦU RA MÔN HỌC (Course learning outcomes)

Bảng 2. (NT: Nhận thức, KN: Kỹ năng, TĐ: Thái độ)

| **CĐRMH** **\[1\]** | **LOs** **\[2\]** | **Mô tả CĐRMH** **\[3\]** | **Cấp độ CĐR Môn học** **\[4\]** |
| --- | --- | --- | --- |
| **G1.1** | 2.7 | Mô tả được các khái niệm cơ bản về CSDL phân tán: \- Xử lý dữ liệu phân tán \- CSDL phân tán, các đặc điểm của CSDL phân tán, kiến trúc hệ quản trị cơ CSDL phân tán, lợi ích của CSDL phân tán,... \- Các thành phần cơ bản trong một hệ quản trị CSDL phân tán (như Oracle hoặc SQL Server). | NT3 |
| **G1.2** | 2.7 | Hiểu rõ các kiến trúc của hệ quản trị CSDL phân tán. | NT3 |
| **G2.1** | 4.1 4.2 | Kỹ năng về thu thập các thông tin cho bài toán phân mảnh và thiết kế được kiến trúc phân mảnh dữ liệu. \- Mô tả bài toán phân mảnh \- Thiết kế các phân mảnh ngang, phân mảnh ngang dọc, phân mảnh hỗn hợp \- Ước lượng hiệu quả của giải pháp \- Tổng hợp, khuyến nghị kiến trúc phân mảnh CSDL | KN3 |
| **G2.2** | 4.1 | Kỹ năng thiết kế định vị các hệ cơ sở dữ liệu phân tán vào bài toán thực tế. | KN3 |
| **G2.3** | 4.1 | Kỹ năng xử lý dữ liệu ứng với các mức trong suốt khác nhau. | KN3 |
| **G2.4** | 4.1 | Kỹ năng tối ưu hóa câu truy vấn trong môi trường phân tán. \- Hiểu được các khái niệm liên quan đến tối ưu hoá câu truy vấn \- Đề xuất giải pháp tối ưu hoá câu truy vấn | KN3 |
| **G2.5** | 4.1 | Kỹ năng về quản lý giao dịch và điều khiển đồng thời phân tán, vấn đề tương tranh và hiệu năng xử lý phân tán. \- Nắm rõ về khái niệm giao dịch, xử lý tương tranh trong môi trường phân tán và lý thuyết giải quyết tương tranh; \- Xác định và mô tả được các bài toán giải quyết tương tranh trong truy vấn phân tán. | KN3 |
| **G3.1** | 4.1 | Vận dụng kỹ năng hình thành ý tưởng, thiết kế (mô hình hóa) và xây dựng hệ thống để giải quyết một bài toán cụ thể trong môi trường phân tán. | KN3 |
| **G3.2** | 4.1 4.2 | Vận dụng được kỹ thuật xử lý phân tán và cách triển khai CSDL phân tán bằng Oracle/SQL Server. \- Cài đặt demo một hệ thống CSDL phân tán; Cài đặt demo một số xử lý truy vấn phân tán; Cài đặt demo một số cơ chế giải quyết tương tranh; \- Kiểm tra và đánh giá hiệu quả các yêu cầu của hệ thống đã cài đặt | KN3 |
| **G4.1** | 5.1 5.2 5.3 5.4 5.5 5.6 | Vận dụng kỹ năng làm việc nhóm: \- Lập lịch biểu làm việc \- Xác định mục tiêu và những việc phải làm \- Vận dụng các quy tắc làm việc nhóm \- Vận dụng các quy tắc giao tiếp nhóm \- Đề xuất các giải pháp \- Thể hiện tinh thần hợp tác nghiêm túc, thương lượng, thỏa thuận, điều chỉnh các xung đột | KN3 |

## NỘI DUNG, KẾ HOẠCH GIẢNG DẠY

**Lý thuyết**

Bảng 3

| **Tuần/Thời lượng** | **Nội dung** | **Hoạt động dạy và học** | **Chuẩn đầu ra** | **Thành phần** **đánh giá** |
| --- | --- | --- | --- | --- |
| **1** **(4 tiết)** +------------------------------------------------------------------+                                                                                                              +------------------+ | **Chương 1. Tổng quan về CSDL phân tán** - Xử lý phân tán - Định nghĩa CSDL phân tán. - Các đặc điểm của CSDL phân tán so với CSDL tập trung. - Tại sao sử dụng CSDL phân tán. - Hệ quản trị CSDL phân tán. - Triển vọng của các hệ cơ sở dữ liệu phân tán. - Phân mảnh dữ liệu (Fragmentation) - Các loại truy xuất CSDL phân tán **Chương 2. Kiến trúc của hệ quản trị CSDLPT** - Kiến trúc tham khảo cho cơ sở dữ liệu phân tán - Các thành phần của hệ quản trị cơ sở dữ liệu phân tán - Kiến trúc của hệ quản trị cơ sở dữ liệu phân tán | **Dạy:** cho các ví dụ, đặt câu hỏi, thuyết giảng **Học ở lớp:** sử dụng tư duy và dựa trên các kiến thức đã học để trả lời câu hỏi, tham gia xây dựng bài học **Học ở nhà:** Ôn tập và tự tìm hiểu trước các khái niệm đã học | **G1.1** **G1.2** |  |
| **2** | **Chương 3. Thiết kế các hệ cơ sở dữ liệu phân tán** - Giới thiệu - Mục tiêu của thiết kế CSDL phân tán - Các bước thiết kế CSDL phân tán - Các chiến lược phân tán dữ liệu - Các phương pháp thiết kế CSDL phân tán - Khái niệm phân mảnh và các quy tắc phân mảnh. - Lý thuyết phân mảnh ngang trong mô hình quan hệ - Lý thuyết phân mảnh dọc không tổn thất thông tin. | **Dạy:** thuyết giảng, phân tích. **Học ở lớp:** nghe giảng, phát biểu ý kiến **Học ở nhà:** ôn bài | **G2.1** **G3.1** |  |
| **3** **4** | - Thiết kế phân mảnh - Thiết kế định vị dữ liệu <!-- --> - Cấp phát tài nguyên trong hệ phân tán | **Dạy:** thuyết giảng, phân tích, làm bài tập mẫu **Học ở lớp:** nghe giảng, phát biểu ý kiến, làm bài tập. **Học ở nhà:** ôn bài, làm bài tập cá nhân **Dạy:** thuyết giảng, phân tích, làm bài tập mẫu **Học ở lớp:** nghe giảng, phát biểu ý kiến, làm bài tập. **Học ở nhà:** ôn bài, làm bài tập cá nhân | **G2.1** **G3.1** **G2.2** | **A1.1** |
| **5** **6** | **Chương 4. Tính trong suốt phân tán** - Tính trong suốt phân tán của ứng dụng chỉ đọc - Tính trong suốt phân tán đối với các ứng dụng cập nhật > \- Các nguyên tắc truy xuất cơ sở dữ liệu phân tán **Chương 4. Tính trong suốt phân tán** - Tính trong suốt phân tán của ứng dụng chỉ đọc - Tính trong suốt phân tán đối với các ứng dụng cập nhật > \- Các nguyên tắc truy xuất cơ sở dữ liệu phân tán | **Dạy:** thuyết giảng **Học ở lớp:** nghe giảng, phát biểu ý kiến **Học ở nhà:** ôn bài, làm bài tập cá nhân **Dạy:** thuyết giảng **Học ở lớp:** nghe giảng, phát biểu ý kiến **Học ở nhà:** ôn bài, làm bài tập cá nhân | **G2.3** **G2.3** | **A1.2** |
| **7** | **Chương 5. Tối ưu hóa truy vấn phân tán** - Khái niệm về truy vấn - Mục tiêu của truy vấn - Các phép toán đại số quan hệ - Đặc trưng của xử lý truy vấn - Phân lớp xử lý truy vấn | **Dạy:** thuyết giảng, phân tích, làm bài tập mẫu **Học ở lớp:** nghe giảng, phát biểu ý kiến **Học ở nhà:** ôn bài | **G2.4** |  |
| **8** **9** | - Phân rã truy vấn - Cục bộ hóa dữ liệu phân tán - Tối ưu hóa truy vấn phân tán - Các thuật toán tối ưu hóa truy vấn phân tán | **Dạy:** thuyết giảng, phân tích, làm bài tập mẫu **Học ở lớp:** nghe giảng, phát biểu ý kiến, làm bài tập. **Học ở nhà:** ôn bài, làm bài tập cá nhân **Dạy:** thuyết giảng, phân tích, làm bài tập mẫu **Học ở lớp:** nghe giảng, phát biểu ý kiến, làm bài tập. **Học ở nhà:** ôn bài, làm bài tập cá nhân | **G2.4** **G2.4** **G3.1** **G2.4** | **A1.3** |
| **10** | **Chương 6. Quản lý giao dịch và điều khiển đồng thời phân tán** - Định nghĩa giao dịch - Đặc trưng của giao dịch - Các tính chất giao dịch - Các loại giao dịch - Điều khiển đồng thời phân tán | \- Seminar bắt buộc | **G2.5** **G3.1** **G3.2** **G4.1** |  |
| **11** | ### Ôn tập cuối kỳ | \- Seminar Chương 6 \- Ôn tập | **G2.5** **G3.1** **G3.2** **G4.1** |  |


**Thực hành**

Bảng 4

| **Tuần\** (5 tiết) | **Nội dung** | **CĐR** **MH** | **Hoạt động dạy và học** | **Thành phần đánh giá** |
| --- | --- | --- | --- | --- |
| **1** | **Giới thiệu nội dung thực hành\ Ôn tập kiến thức về Oracle\** - Tạo bảng, quan hệ, ràng buộc, truy vấn\ - Trigger, Function, Stored Procedure\ - Phân quyền | G1.2\ G3.1\ G3.2 | **Dạy:** ôn tập câu lệnh, demo thao tác\ **Học ở lớp:** theo dõi, xem tài liệu và thực hành trên máy\ **Học ở nhà:** đọc thêm tài liệu, thực hành thêm các truy vấn, Stored Procedure và phân quyền trên Oracle | **A2.1** |
| **2** | **Hướng dẫn thiết kế phân mảnh dữ liệu và kết nối một chiều**\ - Thiết kế phân mảnh dữ liệu\ - Tạo kết nối một chiều bằng database link\ - Viết hàm, thủ tục, ràng buộc toàn vẹn, truy vấn trên môi trường phân tán \- Viết câu truy vấn trong suốt phân tán | G2.1\ G2.2\ G2.3\ G3.1\ G3.2\ G4.1 | **Dạy:** thuyết giảng, ôn tập câu lệnh, làm mẫu thao tác\ **Học ở lớp:** theo dõi, xem tài liệu và thực hành trên máy\ **Học ở nhà:** đọc thêm tài liệu, làm lại bài thực hành | **A2.2** |
| **3** | **BÀI TẬP LỚN 1: THIẾT KẾ PHÂN MẢNH VÀ KẾT NỐI MỘT CHIỀU**\ - Thiết kế cơ sở dữ liệu phân tán cho một đề bài thực tế\ - Tạo kết nối một chiều bằng database link\ - Viết hàm, thủ tục, ràng buộc toàn vẹn, truy vấn trên môi trường phân tán cho đề bài thực tế | G2.1\ G2.2\ G2.3\ G3.1\ G3.2\ G4.1 | **Dạy:** theo dõi công việc của các nhóm; nhắc lại lý thuyết; hỗ trợ SV khi cần\ **Học ở lớp:** thực hiện phân tích, cài đặt hệ thống theo bài toán đã cho\ **Học ở nhà:** tìm hiểu tài liệu bổ sung cho các nội dung đã phân tích, cài đặt. | **BTL1** **(Bài tập lớn)** |
| **4** | **Hướng dẫn kết nối cơ sở dữ liệu phân tán hai chiều**\ - Ôn tập kết nối một chiều\ - Tạo kết nối hai chiều bằng database link\ - Viết hàm, thủ tục, ràng buộc toàn vẹn, truy vấn trên môi trường phân tán \- Viết câu trung vấn tối ưu | G2.1\ G2.2\ G2.3\ G3.1\ G3.2\ G4.1 | **Dạy:** thuyết giảng, ôn tập câu lệnh, làm mẫu thao tác\ **Học ở lớp:** theo dõi, xem tài liệu và thực hành trên máy\ **Học ở nhà:** đọc thêm tài liệu, làm lại bài thực hành | **A2.3** |
| **5** | **BÀI TẬP LỚN 2: KẾT NỐI CƠ SỞ DỮ LIỆU PHÂN TÁN HAI CHIỀU**\ - Thiết kế cơ sở dữ liệu phân tán cho một đề bài thực tế\ - Tạo kết nối hai chiều bằng database link\ - Viết hàm, thủ tục, ràng buộc toàn vẹn, truy vấn trên môi trường phân tán cho đề bài thực tế | G2.1\ G2.2\ G2.3\ G3.1\ G3.2\ G4.1 | **Dạy:** theo dõi công việc của các nhóm; nhắc lại lý thuyết; hỗ trợ SV khi cần\ **Học ở lớp:** thực hiện phân tích, cài đặt hệ thống theo bài toán đã cho\ **Học ở nhà:** tìm hiểu tài liệu bổ sung cho các nội dung đã phân tích, cài đặt. | **BTL2** |
| **6** | **BÀI TẬP LỚN 3: CƠ CHẾ PHÂN TÁN TRONG HỆ QUẢN TRỊ NOSQL**\ Giới thiệu về hệ quản trị cơ sở dữ liệu NoSQL\ - Lịch sử ra đời, nguồn gốc\ - Mô hình lưu trữ\ - Ngôn ngữ thao tác với dữ liệu\ - Minh họa CRUD\ - Cơ chế phân tán\ Cài đặt mô phỏng và thực nghiệm truy vấn phân tán\ - Trình bày quy trình cài đặt phân tán\ - Mô tả bài toán, dữ liệu sử dụng để thực nghiệm\ - Tiến hành truy vấn phân tán\ Viết báo cáo BTL3 | G2.1\ G2.2\ G2.3\ G3.1\ G3.2\ G4.1 | **Dạy:** theo dõi công việc của các nhóm; nhắc lại lý thuyết; hỗ trợ SV khi cần\ **Học ở lớp:** thực hiện phân tích, cài đặt hệ thống theo bài toán đã cho\ **Học ở nhà:** tìm hiểu tài liệu bổ sung cho các nội dung đã phân tích, cài đặt. | **BTL3** |


## ĐÁNH GIÁ MÔN HỌC (Course assessment)

Bảng 5

| **Thành phần đánh giá** | **Nội dung** | **CĐRMH** | **Tỷ lệ %** |
| --- | --- | --- | --- |
| **Thực hành** +------------------------------------------------+ | \- Quá trình: Bài tập cá nhân A1.1, A1.2, A1.3 A1.1: Thiết kế phân mảnh A1.2: Viết câu truy vấn trong suốt A1.3: Viết câu truy vấn tối ưu \- Bài tập lớn (làm nhóm): BTL1, BTL2, BTL3 | G1, G2, G3, G4 | **30%** |
| **Thi giữa kỳ** | **Thi tự luận giữa kỳ** | G2, G3 | **20%** |
| **Thi lý thuyết cuối kỳ** | **Thi tự luận cuối kỳ** | G2, G3 | **50%** |


## 

## ĐÁNH GIÁ MÔN HỌC CHI TIẾT 

Bảng 6


   **Rubric criteria/Mục tiêu môn học**                                                   **Từ 9 đến 10**                                                                                                **Từ 7 đến \<9**                                                                            **Từ 5 đến \<7**                                                                       **Từ 3 đến \<5**                                                                                                                     **\<3**

                  **G1**                  Các khái niệm được mô tả với sự hiểu biết rất cơ bản, hầu hết chính xác và đưa các ví dụ kèm giải thích rõ ràng.        Các khái niệm được mô tả với sự hiểu biết rất cơ bản, hầu hết chính xác và đưa được các ví dụ.        Các khái niệm được mô tả với sự hiểu biết rất cơ bản và hầu hết chính xác.      Các khái niệm được mô tả với sự hiểu biết rất cơ bản và một số khái niệm chưa chính xác.                                                          Hiểu các khái niệm không đầy đủ hoặc thiếu chính xác.

                  **G2**                                    Thu thập các thông tin cho bài toán phân mảnh đầy đủ, chính xác và tối ưu.\                               Thu thập các thông tin cho bài toán phân mảnh đầy đủ và chính xác nhưng chưa tối ưu.\                Thu thập các thông tin cho bài toán phân mảnh đầy đủ và chính xác.\                     Thu thập các thông tin cho bài toán phân mảnh đầy đủ và chính xác.\                                                             Thu thập các thông tin cho bài toán phân mảnh đầy đủ và chính xác.\
                                            Xác định và mô tả được bài toán phân tán, chọn lựa kiến trúc phân tán, chọn lựa hệ quản trị CSDL phân tán;\                 Xác định và mô tả được bài toán phân tán chính xác, chọn lựa kiến trúc phân tán.\                        Xác định và mô tả được bài toán phân tán khá chính xác.\                                  Xác định và mô tả bài toán phân tán ở mức cơ bản.\                                                                    Xác định và mô tả bài toán phân tán không đầy đủ hoặc thiếu chính xác.\
                                                                               Đạt được các tiêu chuẩn ở mức Khá và:\                                                                     Đạt được các tiêu chuẩn ở mức Trung bình và:\                                                   Đạt được các tiêu chuẩn ở mức Yếu và:\                                                 Đạt được các tiêu chuẩn ở mức Kém và:\                                                                                   Hiểu các kỹ thuật phân mảnh: ngang, dọc và hỗn hợp;\
                                                                              - Ước lượng phương án thiết kế phù hợp.\                                                              - Thực hiện phân tích định lượng các phương án thiết kế;\                                           - Lựa chọn kỹ thuật phân mảnh thích hợp;\                                                      - Hiểu kỹ thuật nhân bản;\                                                                                                Hiểu các khái niệm trong suốt dữ liệu.\
                                                             - Biết cách xử lý dữ liệu ứng với các mức "Trong suốt ánh xạ địa phương".\                                         - Biết cách xử lý dữ liệu ứng với các mức "Trong suốt về vị trí".\                          - Biết cách xử lý dữ liệu ứng với các mức "Trong suốt phân đoạn".\                       - Biết cách xử lý dữ liệu ứng với các mức "Không trong suốt".\                                                    Hiểu được các khái niệm liên quan đến tối ưu hoá câu truy vấn trong môi trường tập trung.\
                                                              - Hiện thực yêu cầu tối ưu hoá câu truy vấn ở mức "Tối ưu hóa cục bộ".\                                       - Hiện thực yêu cầu tối ưu hoá câu truy vấn ở mức "Tối ưu hóa toàn cục".\                                 - Đề xuất giải pháp tối ưu hoá câu truy vấn.\                    - Hiểu được các khái niệm liên quan đến tối ưu hoá câu truy vấn trong môi trường phân tán.\                                                                   Hiểu rõ về khái niệm giao dịch.
                                                             - Mô tả được các bài toán giải quyết tương tranh trong truy vấn phân tán.                                        Xác định các bài toán giải quyết tương tranh trong truy vấn phân tán.                                       Biết lý thuyết giải quyết tương tranh.                                    Hiểu rõ về khái niệm xử lý tương tranh trong môi trường phân tán                  

                  **G3**                                                       Đạt được các tiêu chuẩn ở mức Khá và:\                                                                     Đạt được các tiêu chuẩn ở mức Trung bình và:\                                                   Đạt được các tiêu chuẩn ở mức Yếu và:\                                                 Đạt được các tiêu chuẩn ở mức Kém và:\                                                                          Xác định nhu cầu phân tán CSDL cho tổ chức, doanh nghiệp (khách hàng);\
                                                                             - Xác định mức độ phù hợp của công nghệ;\                                       - Chọn lựa các kỹ thuật, công nghệ phân tán CSDL, xử lý phân tán, xử lý tương tranh, replicate dữ liệu;\        - Xác định các chức năng cần thiết của hệ thống CSDL phân tán;\           - Đề xuất kiến trúc phân tán CSDL và hệ quản trị CSDL phân tán phù hợp nhu cầu khách hàng.\     Hiểu các khái niệm cơ bản trong một hệ quản trị CSDL phân tán (Oracle hoặc SQL Server) và có thể thực hiện thao tác Tạo bảng, quan hệ, ràng buộc, truy vấn;
                                                                           - Xác định kiến trúc hệ thống CSDL phân tán.\                                                                  - Cài đặt demo một số xử lý truy vấn phân tán;                                                              - Phân quyền\                                                                  - Trigger, Function, Procedure                                   
                                                                       - Cài đặt demo một số cơ chế giải quyết tương tranh;\                                                                                                                                                                       - Tạo database link\                                                                                                                               
                                                                     - Mô tả việc kiểm tra các yêu cầu của hệ thống đã cài đặt                                                                                                                                                          - Cài đặt demo một hệ thống CSDL phân tán;                                                                                                                    

                  **G4**                     Phối hợp rât tốt với nhóm, có vai trò tiên phong, lãnh đạo nhóm, đồng thời khả năng làm việc độc lập cao.                    Phối hợp khá tốt với nhóm, đồng thời khả năng làm việc độc lập cũng khá tốt..                          Phối hợp nhóm tương đối tốt, khả năng làm việc độc lập.             Chỉ làm được những công việc đơn giản, tương đối thụ động, khả năng làm việc độc lập không cao.                                         Không phối hợp được với nhóm, khả năng thích ứng kém/dựa dẫm vào các bạn khác.

## ĐÁNH GIÁ CHUẨN ĐẦU RA

Bảng 7

| **Chuẩn đầu ra theo CTĐT** | **Minh chứng đánh giá** **(Lý thuyết, quá trình)** | **Minh chứng đánh giá** **(Thực hành)** |
| --- | --- | --- |
| 2.7 | \- Thi lý thuyết giữa kỳ |  |
| 4.1 | \- Thi lý thuyết giữa kỳ \- Thi lý thuyết cuối kỳ | \- Bài tập lớn: BTL1, BTL2, BTL3 |
| 4.2 | \- Thi lý thuyết giữa kỳ \- Thi lý thuyết cuối kỳ | \- Bài tập lớn: BTL1, BTL2, BTL3 |
| 5.1, 5.2, 5.3, 5.3, 5.4, 5.5, 5.6 |  | \- Bài tập lớn: BTL1, BTL2, BTL3 |


## QUY ĐỊNH CỦA MÔN HỌC

- Sinh viên (SV) dành nhiều thời gian để chủ động trong việc tự học và tự tìm hiểu thêm các tài liệu liên quan dưới sự hướng dẫn của Giáo Viên.

- Thực hiện các bài tập nhóm (nhóm tối đa 4 SV), bài tập nhóm để phát triển khả năng làm việc nhóm và trình bày.

- Sinh viên vắng quá 30% số buổi học trên lớp sẽ không được tham dự thi lý thuyết.

- SV chủ động ôn tập, làm bài tập về nhà, bài tập lớn và nộp đúng thời hạn yêu cầu. Nộp bài trễ hạn 1 ngày bị trừ 0.25 điểm, trễ hơn 1 ngày xem như không nộp bài tập.

## TÀI LIỆU HỌC TẬP, THAM KHẢO

1.  M. Tamer Özsu, Patrick Valduriez. *Principles Of Distributed Database Systems (4^th^ ed.)*. 2020. Springer

2.  Chhanda Ray. *Distributed Database Systems*. 2009. Pearson Education

3.  Saeed K. Rahimi, Frank S. Haug. *Distributed Database Management Systems: A Practical Approach*. 2010. Wiley

4.  Hector Garcia-Molina, Jeffrey D. Ullman, Jennifer Widom. *Database Systems: The Complete Book (2^nd^ ed.)*. 2013-2014. Pearson Education Limited.

5.  Elmasri & Navathe. *Fundamentals of database systems (7^th^ ed.)*. 2015. Pearson Education, Inc

## PHẦN MỀM HAY CÔNG CỤ HỖ TRỢ THỰC HÀNH

HQTCSDL thương mại (Microsoft SQL Server, Oracle, MySQL, MongoDB...).


   **Trưởng khoa/ bộ môn**                                 **Giảng viên**
