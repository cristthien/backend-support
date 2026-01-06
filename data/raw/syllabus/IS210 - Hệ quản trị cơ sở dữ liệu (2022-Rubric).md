# IS210 -- HỆ QUẢN TRỊ CƠ SỞ DỮ LIỆU



## THÔNG TIN CHUNG

| Tên môn học (tiếng Việt): | **Hệ Quản trị Cơ sở Dữ liệu** |
| --- | --- |
| Tên môn học (tiếng Anh): | **Database Management System** |
| Mã môn học: | **IS210** |
| Thuộc khối kiến thức: | Chuyên ngành |
| Khoa/Bộ môn phụ trách: | Khoa HTTT |
| Giảng viên phụ trách: | ThS. Đỗ Thị Minh Phụng, ThS. Thái Bảo Trân Email: phungdtm@uit.edu.vn, trantb@uit.edu.vn |
| Giảng viên tham gia giảng dạy: | các giảng viên khoa HTTT |
| Số tín chỉ: | 4 TC lý thuyết : 3 TC thực hành :1 |
| Lý thuyết: (tiết) | 45 tiết |
| Thực hành: (tiết) | 30 tiết |
| Tính chất của môn | Bắt buộc đối với sinh viên ngành/chuyên ngành |
| Môn học trước | Cơ sở dữ liệu |


## MÔ TẢ MÔN HỌC(Course description)

Môn học trình bày khái niệm cơ bản về các hệ quản trị cơ sở dữ liệu (HQTCSDL) hiện đại và đặc tính chung của chúng. Đi sâu vào trình bày thành phần của một HQTCSDL quan hệ, nguyên tắc hoạt động của các giao tác, cơ chế quản lý truy xuất đồng thời, an toàn và khôi phục dữ liệu sau sự cố, tối ưu hóa câu truy vấn. Mỗi nội dung trình bày giải pháp cài đặt cụ thể của chúng trên một trong những HQTCSDL quan hệ đã thương mại như MS SQL Server, DB2, Oracle, MySQL,....

Thông qua các bài tập, đồ án, thực hành, sinh viên có thể vận dụng các kiến thức, kỹ năng để giải quyết các bài toán ứng dụng HQTCSDL vào thực tế. Cụ thể, sinh viên có thể sử dụng thành thạo một số công cụ để quản lý và làm việc với HQTCSDL, có thể thành thạo SQL, function, store procedure, trigger, có khả năng liên hệ giữa lý thuyết và cú pháp thực hành tương ứng. Có thể nắm bắt các kỹ thuật quan trọng như sao lưu dữ liệu, phân tích dữ liệu, tối ưu hóa cơ sở dữ liệu qua các công cụ đi kèm hoặc do bên thứ ba cung cấp để hoạt động cùng các HQTCSDL. Ngoài ra, sinh viên cũng được khuyến khích nghiên cứu, thử nghiệm các kỹ thuật xây dựng ứng dụng có sử dụng HQTCSDL quan hệ như là thành phần lưu trữ dữ liệu của ứng dụng.

## MỤC TIÊU MÔN HỌC (Course Goals)

Bảng 1.

| ## Mục tiêu \[1\] | ## Mục tiêu môn học **\[2\]** | **Chuẩn đầu ra trong CTĐT** |
| --- | --- | --- |
| **G1** | Hiểu được các khái niệm cơ bản: HQTCSDL, các mức trừu tượng của dữ liệu, kiến trúc HQTCSDL, giao tác, lịch thao tác, truy xuất đồng thời, an toàn và bảo mật, tối ưu hóa câu truy vấn... | LO2 (2.7) |
| **G2** +------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+ +------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+ +------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+ | \- Kỹ năng xây dựng giao tác tường minh \- Kỹ năng giải quyết được các vấn đề có thể xảy ra khi cho nhiều giao tác thực hiện đồng thời \- Kỹ năng liên quan đến cơ chế an toàn và khôi phục dữ liệu sau sự cố \- Kỹ năng viết câu truy vấn tối ưu | LO4 (4.1, 4.2) |
| **G3** +------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+ | \- Vận dụng thành thạo ngôn ngữ SQL nâng cao, cài đặt được trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) \- Hiện thực yêu cầu tối ưu hoá câu truy vấn trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) | LO4 (4.1, 4.2) |


## CHUẨN ĐẦU RA MÔN HỌC (Course learning outcomes)

Bảng 2. **(NT: Nhận thức, KN: Kỹ năng, TĐ: Thái độ)**

**\**

| **CĐRMH** **\[1\]** | **LOs \[2\]** | **Mô tả CĐRMH \[3\]** | **Cấp độ CĐR Môn học** **\[4\]** |
| --- | --- | --- | --- |
| G1.1 G1.2 G1.3 G1.4 G1.5 | 2.7 | Hiểu được các khái niệm cơ bản: HQTCSDL, các mức trừu tượng của dữ liệu, kiến trúc HQTCSDL,... Hiểu được các khái niệm liên quan đến giao tác, lịch thao tác Hiểu được các vấn đề xảy ra trong truy xuất đồng thời và các kỹ thuật giải quyết Hiểu được các khái niệm liên quan đến cơ chế an toàn và khôi phục dữ liệu sau sự cố Hiểu được các khái niệm liên quan đến tối ưu hóa câu truy vấn | NT3 |
| G2.1 G2.2 G2.3 G2.4 G2.5 G3.1 G3.2 | 4.1 4.1 4.1 4.2 4.1 4.2 4.1 4.2 4.1 4.2 4.1 4.2 | Kỹ năng cơ bản về ngôn ngữ T-SQL nâng cao: cấu trúc điều khiển, cursor, trigger, function, stored procedure. Xây dựng được các giao tác tường minh trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) Xây dựng được cơ chế khoá (Locks), mức cô lập (Isolation Level) và Deadlock_Priority của HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) để giải quyết vấn đề Sao lưu và phục hồi dữ liệu khi hệ thống gặp sự cố trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) Mô tả tiến trình viết câu truy vấn tối ưu Vận dụng được ngôn ngữ T-SQL nâng cao trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) Hiện thực yêu cầu tối ưu hoá câu truy vấn trên một HQTCSDL thương mại (MS SQL Server, Oracle, DB2, MySQL, ...) | KN3 |


## NỘI DUNG CHI TIẾT 

**Lý thuyết**

| **Tuần/Thời lượng** | **Nội dung** | **Ghi chú/Mô tả hoạt động** | **Chuẩn đầu ra** | **Thành phần đánh giá** |
| --- | --- | --- | --- | --- |
| 1 (3 tiết) | ### Chương 1. Kiến trúc một HQTCSDL 1.  Định nghĩa HQTCSDL 2.  Ba mức trừu tượng của dữ liệu 3.  Các đặc trưng của dữ liệu trong HQTCSDL 4.  Kiến trúc HQTCSDL 5.  Các loại HQTCSDL | - Giảng viên đặt vấn đề *(đặt câu hỏi Brainstorming,...),* sinh viên thảo luận. - Giảng viên giảng dạy, tổng kết. - Hình thành nhóm. | G1.1 |  |
| 2 3 | ### Chương 2. T-SQL nâng cao 1.  Khai báo và sử dụng biến trong SQL 2.  Cấu trúc điều khiển trong T-SQL 3.  Cursor 1.  Giới thiệu 2.  Cú pháp 3.  Ví dụ 4.  Trigger 1.  Giới thiệu 2.  Cú pháp 3.  Ví dụ 1.  Function 1.  Giới thiệu 2.  Cú pháp 3.  Ví dụ 2.  Stored Procedure 2.6.1 Giới thiệu 2.6.2 Cú pháp 2.6.3 Ví dụ | - Giảng viên đặt vấn đề. - Giới thiệu cấu trúc điều khiển trong T-SQL, cursor, trigger. - Giảng giải, giải thích-minh họa. - Đề xuất giải pháp - Giảng viên tổng kết, kết luận. - Sửa bài tập A1 - Giảng viên đặt vấn đề - Giới thiệu function, stored procedure - Giảng giải, giải thích-minh họa - Đề xuất giải pháp - Giảng viên tổng kết, đánh giá, kết luận | G2.1 G3.1 G2.1 G3.1 | A1.1 |
| 4 5 6 | ### Chương 3. Giao tác 1.  Giới thiệu 2.  Khái niệm giao tác (transaction) 1.  Định nghĩa 2.  Tính chất ACID của giao tác 3.  Các thao tác của giao tác 4.  Trạng thái của giao tác 3.  Lịch thao tác (schedule) 1.  Giới thiệu 2.  Định nghĩa 3.  Lịch tuần tự (Serial schedule) 1.  Lịch khả tuần tự (Serializable schedule) Lịch khả tuần tự xung đột (conflict-serializable) 1.  Lịch khả tuần tự (tt) Lịch khả tuần tự view (view-serializable) | - Sửa bài tập A1 - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận - Giảng viên đặt vấn đề*.* - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, kết luận. - Sửa bài tập A2 - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận | G1.2 G2.2 G3.1 G1.2 G2.2 G3.1 G1.2 G2.2 G3.1 | A1.2 |
| 7 | ### Chương 4. Điều khiển truy xuất đồng thời 1.  Các vấn đề trong truy xuất đồng thời 1.  Mất dữ liệu đã cập nhật (lost updated) 2.  Không thể đọc lại (unrepeatable read) 3.  "Bóng ma" (phantom) 4.  Đọc dữ liệu chưa chính xác (dirty read) 2.  Kỹ thuật khóa (locking) 1.  Giới thiệu 2.  Khóa 2 giai đoạn (two-phase) 3.  Khóa đọc viết 4.  Khóa đa hạt (multiple granularity) 5.  Nghi thức cây (tree protocol) | - Sửa bài tập A2 - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Đề xuất giải pháp - Giảng viên tổng kết | G1.3 G2.3 G3.1 | A1.3 |
| 8 9 10 | 1.  Kỹ thuật nhãn thời gian (timestamps) 1.  Giới thiệu 2.  Nhãn thời gian toàn phần 3.  Nhãn thời gian riêng phần Nhãn thời gian nhiều phiên bản (multiversion) 1.  Kỹ thuật xác nhận hợp lệ (validation) 2.  Quay lui dây chuyền (cascading rollback) 3.  Lịch khả phục hồi (recoverable schedule) 1.  Deadlock | - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận \- Giảng viên đặt vấn đề \- Giảng giải, giải thích-minh họa \- Đề xuất giải pháp \- Seminar chủ đề Deadlock: giả lập để thấy deadlock và cách hệ quản trị xử lý khi có deadlock xảy ra. \- Giảng viên tổng kết | G1.3 G2.3 G3.1 G1.3 G2.3 G3.1 G1.3 G2.3 G3.1 |  |
| 11 12 | ### Chương 5. Phục hồi dữ liệu khi có sự cố - An toàn dữ liệu 1.  Giới thiệu 2.  Phân loại sự cố 3.  Mục tiêu của khôi phục sự cố 4.  Nhật ký giao tác (transaction log) 5.  Điểm lưu trữ (checkpoint) 1.  Checkpoint đơn giản 2.  Checkpoint linh động (nonquiescent checkpoint) 5.6 Phương pháp khôi phục 5.6.1. Undo-Logging (immediate modification) 5.6.2. Redo-Logging (deferred modification) 5.6.3. Undo/Redo Logging | - Sửa bài tập - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận | G1.4 G2.4 G3.1 G1.4 G2.4 G3.1 | A1.4 |
| 13 14 | ### Chương 6. Tối ưu hóa câu hỏi 1.  Xử lý câu truy vấn 6.1.1. Giới thiệu 6.1.2. Bộ biên dịch câu truy vấn (query compiler) 6.1.3. Phân tích cú pháp 6.1.4. Chuyển cây phân tích sang ĐSQH 6.1.5. Qui tắc tối ưu cây truy vấn 6.1.6. Ước lượng chi phí 1.  Tối ưu hoá câu truy vấn 1.  Giới thiệu 2.  Kế hoạch truy vấn 3.  Kế hoạch cho phép chọn 4.  Kế hoạch cho phép kết | - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết - Giảng viên đặt vấn đề - Giảng giải, giải thích-minh họa - Giảng viên tổng kết, đánh giá, kết luận | G1.5 G2.5 G3.2 G1.5 G2.5 G3.2 | A1.5 |
| 15 | **Ôn tập** | - Sinh viên đặt câu hỏi, Giải đáp, nêu lỗi thường gặp. |  |  |


**Thực hành**

| **Buổi học (5 tiết)** | **Nội dung** | **CĐRMH** | **Hoạt động dạy và học** | **Thành phần đánh giá** |
| --- | --- | --- | --- | --- |
| 1 | Các lệnh Transact-SQL: cấu trúc điều khiển, cursor, trigger, function, stored procedure. | G2.1 G3.1 | - Hướng dẫn thực hành chủ đề cấu trúc điều khiển, cursor, trigger, function, stored proc - Bài tập tình huống theo nhóm trên lược đồ Cơ sở dữ liệu Quản lý thư viện - Đề xuất giải pháp - Giảng viên tổng kết, kết luận - **Học ở nhà**: sinh viên xây dựng các trigger, stored proc trong đồ án môn học | Đồ án môn học (A2) A2.1 |
| 2 | - Xây dựng giao tác tường minh trên SQL-Server: ý nghĩa, cách sử dụng & các lệnh liên quan | G1.2 G2.2 G3.1 | - Hướng dẫn thực hành chủ đề transaction - Bài tập tình huống theo nhóm trên lược đồ Cơ sở dữ liệu Quản lý thư viện (xây dựng các giao tác cho tất cả stored procedure trong mục 4 và tất cả trigger trong mục 5 bài Quản lý thư viện)) - Đề xuất giải pháp - Giảng viên tổng kết, kết luận - **Học ở nhà**: sinh viên xây dựng các giao tác trong đồ án môn học | A2 A2.2 |
| 3 | - Quản lý truy cập dữ liệu đồng thời: Vấn đề gặp phải khi có nhiều giao tác truy cập đồng thời, cách giải quyết bằng cơ chế khóa (Locks) và bằng mức cô lập (Isolation Level). | G1.3 G2.3 G3.1 | - Hướng dẫn thực hành chủ đề Locks và Isolation Level - Bài tập tình huống theo nhóm trên lược đồ Cơ sở dữ liệu Quản lý thư viện <!-- --> - Giả lập các giao tác theo kịch bản cho trước và theo dõi bằng sp_lock để thấy hoạt động của các loại khóa. - Sử dụng Isolation Level và Lock Mode cho bài tập quản lý thư viện. Yêu cầu sinh viên phát hiện tất cả các trường hợp xử lý đồng thời và đề nghị cách giải quyết. Đề xuất giải pháp <!-- --> - Giảng viên tổng kết, kết luận - Học ở nhà: với các giao tác đã xây dựng ở các tuần trước, sinh viên tự nhận diện các vấn đề có thể xảy ra khi cho chúng thực hiện đồng thời và xác định mức cô lập/ cơ chế khóa phù hợp để khắc phục trong đồ án môn học. | A2 A2.3 |
| 4 | - Vấn đề deadlock: các trường hợp gây deadlock khi xác lập khóa. Giả lập để thấy deadlock và cách hệ quản trị xử lý khi có deadlock xảy ra (dùng set deadlock_priority). Một số giải pháp hạn chế deadlock. | G1.3 G2.3 G3.1 | - Bài tập tình huống theo nhóm trên lược đồ Cơ sở dữ liệu Quản lý thư viện (với các giao tác đã thiết lập khóa, sinh viên tự nhận diện giao tác nào có khả năng gây ra deadlock khi cho thực hiện đồng thời). - Đề xuất giải pháp - Giảng viên tổng kết, kết luận - **Học ở nhà**: với các giao tác đã thiết lập khóa, sinh viên tự nhận diện giao tác nào có khả năng gây ra deadlock khi cho thực hiện đồng thời trong đồ án môn học. | A2 A2.3 |
| 5 | - Vận dụng các kiến thức đã học vào bài tổng hợp/đồ án cuối kỳ. | G3.1 G3.2 | - Phát triển ứng dụng thực tế minh hoạ, hỗ trợ nhiều người dùng cùng lúc sao cho: <!-- --> - Ngăn chặn tốt các vấn đề, không để xảy ra trình trạng không nhất quán trong dữ liệu. <!-- --> - Tạo thuận tiện và giảm tối đa thời gian chờ cho người sử dụng hệ thống | A2 |


## ĐÁNH GIÁ MÔN HỌC (Course assessment)

| **Thành phần đánh giá** | **Nội dung** | **CĐRMH** | **Tỷ lệ %** |
| --- | --- | --- | --- |
| **Thực hành** | **\*Đồ án môn học (A2)** Tìm hiểu cách xây dựng các ứng dụng có sử dụng các tính năng giao tác của HQTCSDL quan hệ, xây dựng demo. **\* Quá trình:** **-** Bài tập cá nhân: A1.1, A1.2, A1.3, A1.4, A1.5 | G1, G2, G3 | 30% |
| **Lý thuyết** **Giữa Kỳ** | **Thi tự luận giữa kỳ (A3)** | G1, G2, G3 | 20% |
| **Lý thuyết** **Cuối Kỳ** | **Thi tự luận cuối kỳ (A4)** | G2, G3 | 50% |


## ĐÁNH GIÁ MÔN HỌC CHI TIẾT 

| **Rubric criteria/Mục tiêu môn học** | **Từ 0 đến \<3** | **Từ 3 đến \<5** | **Từ 5 đến \<7** | **Từ 7 đến \<9** | **Từ 9 đến 10** |
| --- | --- | --- | --- | --- | --- |
| **G1** | Chưa nắm rõ đa số các khái niệm, chưa hiểu rõ hoặc hiểu không chính xác các kiến thức nền tảng. | Nắm được các khái niệm ở mức cơ bản. Một số khái niệm hiểu chưa chính xác. | Nắm được các khái niệm cơ bản. Hầu hết các khái niệm đều hiểu chính xác. | Nắm được các khái niệm cơ bản. Hầu hết các khái niệm đều hiểu chính xác và đưa ra được ví dụ. | Nắm được các khái niệm cơ bản. Hầu hết các khái niệm đều hiểu chính xác, giải thích cặn kẽ và đưa ra được ví dụ cụ thể. |
| **G2** | \- Không nắm căn bản vể ngôn ngữ, không có khả năng áp dụng ngôn ngữ SQL để giải quyết các bài toán theo yêu cầu.. \- Không hiểu về giao tác và hoạt động của chúng trong HQTCSDL. -Không biết rõ cách mà HQTCSDL quản lý các giao tác đồng thời. Không hiểu khả năng phục hồi và tái lập dữ liệu của HQTCSDL sau khi gặp sự cố. | \- Nắm sơ lược về ngôn ngữ, nhưng không thể áp dụng giải quyết các bài toán đề ra, chỉ có thể làm lại với các yêu cầu tương tự. \- Chưa hiểu rõ cách thức hoạt động của giao tác, tuy nhiên có những khái niệm ban đầu -Có khái niệm về điều khiển đồng thời, có thể làm lại bài tập trong bài giảng lý thuyết, tuy nhiên chưa thể giải quyết các yêu cầu đề ra. Chỉ làm được những bài tập cơ bản, quen thuộc. | \- Có thể sử dụng SQL để giải quyết các vấn đề đơn giản và chưa thành thục các chức năng SQL nâng cao -Hiểu cách thức giao tác vận hành và bản chất lý thuyết về giao tác. \- Triển khai được các giao tác trong ngôn ngữ SQL. \- Có khả năng giải quyết các yêu cầu đề ra trên cơ sở lý thuyết. \- Chưa biết cách áp dụng trong thực hành. Có khả năng giải quyết các bài tập tương tự nhưng không hiểu sâu để giải quyết các vấn đề mở rộng hơn. | \- Hiểu bài toán, có thể vận dụng để giải quyết vấn đề tốt, tuy nhiên chưa tối ưu. -Nắm vững và triển khai các giao tác trong SQL để giải quyết các yêu cầu đề ra. \- Có thể giải quyết các bài toán đề ra về điều khiển đồng thời, vận dụng vào thực nghiệm. Có khả năng giải quyết các bài tập lý thuyết nâng cao vận dụng để tự tìm giải pháp. | Hiểu rõ, chính xác yêu cầu từng bài toán, vận dụng SQL giải quyết vấn đề thông minh, tối ưu. \- Có khả năng tối ưu các xử lý trong giao tác và giải các yêu cầu khó, có khả năng sử dụng giao tác với ứng dụng tự xây dựng. -Tối ưu hóa các thực nghiệm, giải quyết các yêu cầu có tính hiểu bài cao. . Vận dụng lý thuyết trong thực hành và thành thục các thao tác trên HQT. |
| **G3** | \- Không nắm căn bản về khả năng áp dụng ngôn ngữ SQL để giải quyết các bài toán quản lý thực tế theo yêu cầu. Chưa biết cách tối ưu hóa các câu truy vấn SQL | \- Nắm sơ lược về ngôn ngữ, nhưng không thể áp dụng giải quyết các bài toán quản lý thực tế. Biết về tối ưu hóa các câu truy vấn tuy nhiên chỉ ở mức độ nắm kiến thức | \- Có thể sử dụng SQL để giải quyết các vấn đề đơn giản trong bài toán quản lý thực tế và chưa thành thục các chức năng SQL nâng cao Có khả năng vận hành và làm các bài tập mang tính lý thuyết | \- Hiểu bài toán, có thể vận dụng để giải quyết vấn đề tốt, tuy nhiên chưa tối ưu. Có khả năng vận hành vào thực tế các câu truy vấn | Hiểu rõ, chính xác yêu cầu từng bài toán thực tế, vận dụng SQL giải quyết vấn đề thông minh, tối ưu. . Tối ưu được và áp dụng vào thực tiễn |

## ĐÁNH GIÁ CHUẨN ĐẦU RA

| **Chuẩn đầu ra theo CTĐT** | **Minh chứng đánh giá** **(Lý thuyết, quá trình)** | **Minh chứng đánh giá** **(Thực hành)** |
| --- | --- | --- |
| **2.7** | \- Bài thi lý thuyết giữa kỳ | \- Đồ án A2 -- Giới thiệu đồ án và các khái niệm |
| **4.1** | \- Bài tập A1.1, A1.2, A1.3, A1.4 \- Bài thi lý thuyết giữa kỳ \- Bài thi lý thuyết cuối kỳ | Đồ án A2: \- Các chức năng và thành phần của hệ thống. \- Nêu thiết kế CSDL, trình bày cách sử dụng giao tác tường minh. \- Thiết kế giao diện chương trình, cài đặt chương trình. \- Trình bày cách sử dụng store procedure để giải quyết vấn đề, cách ứng dụng làm việc với CSDL |
| **4.2** | \- Bài tập A1.2, A1.3, A1.4, A1.5 \- Bài thi lý thuyết giữa kỳ \- Bài thi lý thuyết cuối kỳ | Đồ án A2: Kiểm tra đối chiếu sự nhất quán, xuyên suốt các mô hình. |

## QUY ĐỊNH CỦA MÔN HỌC (Course requirements and expectations)

- Cách thức hoạt động trong lớp, làm việc nhóm: hình thành nhóm (nhóm tối đa 4 sinh viên- chỉ số tối đa có thể thay đổi tùy theo lớp và giáo viên yêu cầu), nhóm thảo luận, phân công công việc và lập bảng kế hoạch thực hiện để các thành viên nhóm theo dõi, thực hiện báo cáo đồ án môn học và trình bày chi tiết cho giảng viên sau khi kết thúc môn học 1-2 tuần.

- Phương pháp học tập của sinh viên tại lớp, về nhà: thực hành xử lý tình huống tại lớp và làm bài tập, đồ án môn học về nhà.

- Hình thức thi cuối kỳ: tự luận

- Sinh viên không nộp bài tập và báo cáo đúng hạn coi như không nộp bài. Không nộp bài hoặc các bài làm giống nhau sẽ bị 0 điểm*.*

## TÀI LIỆU HỌC TẬP, THAM KHẢO

1.  Slides bài giảng môn Hệ quản trị cơ sở dữ liệu SQL Server, khoa Hệ thống Thông Tin, Đại học Công Nghệ Thông Tin, ĐHQG, HCM.

2.  Tài Liệu hướng dẫn thực hành môn Hệ Quản Trị Cơ Sở Dữ Liệu, ThS Nguyễn thị Kim Phụng và ThS. Đỗ Thị Minh Phụng.

3.  Database Systems: Design, Implementation, and Management (12th Edition) by Carlos Coronel, Steven Morris, Cengage Learning Publisher, 2016.

4.  Hector Garcia-Mollina, Jeffrey D. Ullman, Jennifer Widom. *Database Systems: The Complete Book*. Prentice Hall.

5.  Abraham, Silberschatz, Henry F.Korth, S. Sudarshan. *Database System Concepts*. McGraw-Hill.

6.  Thomas Connolly, Carolyn Begg. *Database Systems.* Addison Wesley.

## PHẦN MỀM HAY CÔNG CỤ HỖ TRỢ THỰC HÀNH

Một trong các HQTCSDL thương mại (Microsoft SQL Server, Oracle, DB2, MySQL...) và các công cụ kèm theo.

| **Trưởng khoa/ bộ môn** (Ký và ghi rõ họ tên) |  | **Giảng viên** (Ký và ghi rõ họ tên) |
| --- | --- | --- |


**ĐÁNH GIÁ QUÁ TRÌNH**

**(BÀI TẬP LÝ THUYẾT CÁ NHÂN A1)**

Mỗi sinh viên tự mình giải quyết các bài tập theo từng phần từ A1.1 \--\> A1.5, trình tự theo quá trình học lý thuyết trên lớp. Với mỗi bài tập, sinh viên làm và giáo viên sẽ gọi ngẫu nhiên trình bày trên lớp cho giáo viên đánh giá và các sinh viên khác tham khảo.

.

**ĐÁNH GIÁ ĐỒ ÁN MÔN HỌC**

**(ĐỒ ÁN A2)**

**Nghiên cứu các tính năng nâng cao của DBMS**

Đồ án yêu cầu sinh viên phát triển một ứng dụng đễ minh họa cho việc kết hợp giữa ứng dụng và CSDL trong xây dựng hệ thống. Trong đó các store procedure, trigger, và các phương thức truy vấn cần được triển khai.

| **STT** | **Nội dung** | **Yêu cầu** |
| --- | --- | --- |
| 1 | Giới thiệu đồ án và các tính năng | Trình bày mục tiêu của ứng dụng, các tính năng chính của ứng dụng |
| 2 | Nêu thiết kế CSDL. | Trình bày về cấu trúc CSDL, các sơ đồ thiết kế liên quan |
| 3 | #### Trình bày cách sử dụng store procedure để giải quyết vấn đề, cách ứng dụng làm việc với CSDL | Trình bày quá trình làm việc của ứng dụng và csdl |
| 4 | Thiết kế giao diện chương trình | Thiết kế giao diện chương trình và mô tả sơ lược chức năng.\ Giao diện đẹp, phù hợp chức năng trình bày. |
| 5 | #### Cài đặt chương trình | Yêu cầu cài đặt được mô hình CSDL quan hệ đã thiết kế.\ Các chức năng của phần mềm cần hiện thực: tối thiểu 2 chức năng quản lý chính, tối thiểu 2 chức năng tìm kiếm, tối thiểu 2 chức năng thống kê, báo cáo và có sử dụng store procedure, trigger, ... |
| 6 | Trình bày báo cáo | Báo cáo trình bày rõ ràng\ Thực hiện theo các qui định trình bày khóa luận tốt nghiệp |

