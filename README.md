# Mock Customer Portal

Cổng khách hàng đơn giản, dùng API của dự án `orders-api`. Fixture kiểm thử whitebox chạy tại localhost, không dùng dữ liệu thật và không dành cho production.

Yêu cầu Python 3.10+, không cần thư viện ngoài. Khởi động `orders-api` trước, sau đó:

```powershell
python app.py
```

Mở `http://127.0.0.1:8765`. Nếu đổi cổng: `python app.py --port 9005 --orders-port 9006`.

Tài khoản giả:

| Người dùng | Mật khẩu mẫu |
| --- | --- |
| alice | demo-alice |
| bob | demo-bob |

`POST /api/login` nhận JSON `username`, `password`, trả bearer token trong bộ nhớ. Các endpoint `/api/orders` và `/api/orders/{id}` yêu cầu token này qua header `Authorization: Bearer <token>`.

Portal chuyển context người dùng đã đăng nhập sang service đơn hàng. Yêu cầu sản phẩm: người dùng chỉ xem được đơn hàng thuộc tài khoản của mình. Tài khoản mẫu công khai là một phần của fixture. Khởi động lại portal sẽ xóa các phiên đăng nhập.
