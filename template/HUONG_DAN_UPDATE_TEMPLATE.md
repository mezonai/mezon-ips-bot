# Hướng dẫn cập nhật Template_HDCG.docx để dùng với docxtpl

## Cần thay đổi các placeholder trong template:

### 1. Thông tin cơ bản (paragraphs)
Thay đổi từ `[field]` sang `{{ field }}`:

- `[dd]` → `{{ dd }}`
- `[mm]` → `{{ mm }}`
- `[yyyy]` → `{{ yyyy }}`
- `[pronoun]` → `{{ pronoun }}`
- `[expert_name]` → `{{ expert_name }}`
- `[nationality]` → `{{ nationality }}`
- `[address]` → `{{ address }}`
- `[id_number]` → `{{ id_number }}`
- `[issued_date]` → `{{ issued_date }}`
- `[issued_place]` → `{{ issued_place }}`
- `[email_address]` → `{{ email_address }}`
- `[phone]` → `{{ phone }}`
- `[bank_account]` → `{{ bank_account }}`
- `[bank_name]` → `{{ bank_name }}`
- `[sum_activities]` → `{{ sum_activities }}`
- `[activity_purpose]` → `{{ activity_purpose }}`
- `[project_name]` → `{{ project_name }}`
- `[end_date]` → `{{ end_date }}`

### 2. Table 1 (Header - Số hợp đồng)
Thay:
```
Số: [order]/[yyyy]/HĐCG-[abbreviated_project]-[additional_information]
```
Thành:
```
Số: {{ order_id }}/{{ yyyy }}/HĐCG-{{ abbreviated_project }}-{{ additional_information }}
```

### 3. Table 2 (Activities) - QUAN TRỌNG!

**Xóa tất cả các row mẫu** (row 2-11), chỉ giữ lại 2 header rows.

Sau đó thêm Jinja2 loop:

**Sau row header thứ 2, thêm:**
```
{% for activity in activities %}
```

**Thêm 2 rows cho mỗi activity:**

Row 1:
| {{ activity.stt }} | {{ activity.activity_number }}. {{ activity.activity_name }} | (merge cells) | (merge cells) | (merge cells) |

Row 2:
| (empty) | {{ activity.budget }} | {{ activity.working_days }} | {{ activity.rate }} | {{ activity.real_amount }} |

**Sau 2 rows trên, thêm:**
```
{% endfor %}
```

**Sau endfor, thêm summary rows:**

Row Tổng cộng:
| Tổng cộng | Tổng cộng | Tổng cộng | Tổng cộng | {{ total_amount }} |

Row Thuế:
| Thuế TNCN 10% giữ lại | (merge) | (merge) | (merge) | {{ tax_amount }} |

Row Thực nhận:
| Tổng tiền thanh toán cho chuyên gia | (merge) | (merge) | (merge) | {{ final_amount }} |

Row Bằng chữ:
| Bằng chữ: | (merge) | (merge) | (merge) | {{ final_amount_text }} |

## Cách edit file Word:

1. Mở `Template_HDCG.docx` bằng Microsoft Word
2. Bật "Show/Hide ¶" để thấy rõ các ký tự đặc biệt
3. Tìm và thay thế tất cả `[field]` thành `{{ field }}`
4. Trong bảng activities:
   - Xóa các row mẫu (giữ 2 header rows)
   - Thêm `{% for activity in activities %}` vào một cell
   - Thêm 2 rows template với `{{ activity.xxx }}`
   - Thêm `{% endfor %}` vào một cell
   - Thêm các summary rows với `{{ total_amount }}`, etc.
5. Lưu file

## Hoặc tôi có thể tạo template mới từ đầu nếu cần!
