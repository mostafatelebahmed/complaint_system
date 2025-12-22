import base64
from datetime import datetime

def get_printable_html(comp, logo_right_path, logo_left_path):
    """
    دالة تقوم بتصميم تقرير الشكوى بصيغة HTML جاهز للطباعة (نسخة محسنة)
    """
    
    # 1. قاموس لترجمة الحالة (عشان تظهر بالعربي)
    STATUS_AR = { 
        "New": "جديد", 
        "In Progress": "جاري التنفيذ", 
        "Resolved": "تم الحل", 
        "Closed": "مغلق",
        "All": "الكل" 
    }
    # الحصول على الحالة بالعربي، لو مش موجودة نعرض الإنجليزي
    status_arabic = STATUS_AR.get(comp.status, comp.status)

    # 2. تحويل الصور
    def img_to_b64(path):
        try:
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except: 
            return ""

    b64_right = img_to_b64(logo_right_path)
    b64_left = img_to_b64(logo_left_path)
    
    date_str = comp.created_at.strftime("%Y-%m-%d %I:%M %p")
    
    # 3. تجهيز سجل المتابعة
    history_rows = ""
    if comp.history:
        for h in sorted(comp.history, key=lambda x: x.timestamp, reverse=True):
            user_name = h.user.full_name if h.user else "System"
            history_rows += f"""
            <tr>
                <td>{h.timestamp.strftime('%Y-%m-%d %I:%M %p')}</td>
                <td>{user_name}</td>
                <td>{h.action}</td>
                <td>{h.details}</td>
            </tr>
            """
    else:
        history_rows = "<tr><td colspan='4' style='text-align:center'>لا يوجد سجل متابعة</td></tr>"

    # 4. كود التصميم (تم تعديل CSS لإزالة الحدود وضبط الطباعة)
    html = f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        /* إعدادات الطباعة الدقيقة لمنع "الأكل" من الصفحة */
        @media print {{
            @page {{ 
                size: A4; 
                margin: 5mm; /* هامش صغير جداً للصفحة */
            }}
            body * {{ visibility: hidden; }}
            #printableArea, #printableArea * {{ visibility: visible; }}
            #printableArea {{ 
                position: absolute; 
                left: 0; 
                top: 0; 
                width: 100%; 
                margin: 0;
                padding: 10px;
            }}
        }}

        /* التصميم العام */
        .report-container {{
            font-family: 'Cairo', sans-serif;
            direction: rtl;
            text-align: right;
            width: 100%;
            max-width: 95%; /* عشان نضمن انه فت في الصفحة */
            margin: auto;
            /* تم حذف الحدود (Border) حسب طلبك */
            background: #fff;
            color: #333;
        }}

        .header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            border-bottom: 3px solid #2c3e50; /* خط فاصل شيك بدلاً من حدود الصفحة */
            padding-bottom: 20px; 
            margin-bottom: 30px; 
        }}
        .header img {{ height: 80px; object-fit: contain; }}
        
        .title-box {{ text-align: center; }}
        .title-box h1 {{ margin: 0; color: #2c3e50; font-size: 26px; font-weight: 800; }}
        .title-box p {{ margin: 5px 0 0; color: #7f8c8d; font-size: 14px; }}
        
        /* تنسيق رقم الشكوى */
        .comp-code {{
            background-color: #f1f2f6;
            color: #c0392b;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 1.2rem;
            font-weight: bold;
            margin-top: 10px;
            display: inline-block;
            border: 1px dashed #c0392b;
        }}

        .info-grid {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; 
            margin-bottom: 30px; 
        }}
        .info-item {{ 
            border-bottom: 1px solid #eee; 
            padding-bottom: 5px; 
        }}
        .label {{ font-weight: bold; color: #2980b9; font-size: 0.95rem; margin-left: 10px; }}
        .value {{ font-size: 1.1rem; font-weight: 600; color: #2c3e50; }}
        
        .section-title {{ 
            background: #ecf0f1; 
            color: #2c3e50; 
            padding: 8px 15px; 
            font-weight: 800; 
            border-right: 5px solid #2980b9; 
            margin: 30px 0 15px; 
            font-size: 1.2rem; 
        }}
        
        .desc-box {{ 
            border: 1px solid #ddd; 
            padding: 20px; 
            border-radius: 8px; 
            background: #fafafa; 
            min-height: 80px; 
            line-height: 1.8; 
            white-space: pre-wrap; 
            font-size: 1.1rem;
        }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.95rem; }}
        th {{ background: #2c3e50; color: white; text-align: right; padding: 10px; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        
        .footer {{ 
            margin-top: 50px; 
            text-align: center; 
            font-size: 0.8rem; 
            color: #aaa; 
            border-top: 1px solid #eee; 
            padding-top: 15px; 
        }}
    </style>
    </head>
    <body>
        <div id="printableArea" class="report-container">
            <div class="header">
                <img src="data:image/png;base64,{b64_right}" alt="Logo">
                <div class="title-box">
                    <h1>نظام إدارة الشكاوى</h1>
                    <p>Unified Complaint Management System</p>
                    <div class="comp-code">رقم الشكوى: {comp.code}</div>
                </div>
                <img src="data:image/png;base64,{b64_left}" alt="Logo">
            </div>
            
            <div class="info-grid">
                <div class="info-item"><span class="label">اسم العميل:</span><span class="value">{comp.customer_name}</span></div>
                <div class="info-item"><span class="label">تاريخ الورود:</span><span class="value">{date_str}</span></div>
                <div class="info-item"><span class="label">رقم الهاتف:</span><span class="value">{comp.phone}</span></div>
                <div class="info-item"><span class="label">المصدر:</span><span class="value">{comp.source}</span></div>
                <div class="info-item"><span class="label">الإدارة المختصة:</span><span class="value">{comp.department.name}</span></div>
                <div class="info-item"><span class="label">المشروع:</span><span class="value">{comp.project.name}</span></div>
                <div class="info-item"><span class="label">الحالة الحالية:</span><span class="value">{status_arabic}</span></div>
            </div>
            
            <div class="section-title">📄 تفاصيل ومحتوى الشكوى</div>
            <div class="desc-box">{comp.description}</div>
            
            <div class="section-title">🕒 سجل المتابعة والردود</div>
            <table>
                <thead><tr><th>التاريخ</th><th>المستخدم</th><th>الإجراء</th><th>التفاصيل</th></tr></thead>
                <tbody>{history_rows}</tbody>
            </table>
            
            <div class="footer">
                تم استخراج هذا التقرير إلكترونياً | تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
            </div>
        </div>
        <script>setTimeout(function() {{ window.print(); }}, 500);</script>
    </body>
    </html>
    """
    return html


def get_printable_html(comp, logo_right_path, logo_left_path):
    STATUS_AR = { "New": "جديد", "In Progress": "جاري التنفيذ", "Resolved": "تم الحل", "Closed": "مغلق", "All": "الكل" }
    status_arabic = STATUS_AR.get(comp.status, comp.status)

    def img_to_b64(path):
        try:
            with open(path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
        except: return ""

    b64_right = img_to_b64(logo_right_path)
    b64_left = img_to_b64(logo_left_path)
    date_str = comp.created_at.strftime("%Y-%m-%d %I:%M %p")
    
    history_rows = ""
    if comp.history:
        for h in sorted(comp.history, key=lambda x: x.timestamp, reverse=True):
            user_name = h.user.full_name if h.user else "System"
            history_rows += f"<tr><td>{h.timestamp.strftime('%Y-%m-%d %I:%M %p')}</td><td>{user_name}</td><td>{h.action}</td><td>{h.details}</td></tr>"
    else: history_rows = "<tr><td colspan='4' style='text-align:center'>لا يوجد سجل متابعة</td></tr>"

    html = f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        /* الحل الجذري لإزالة هيدر المتصفح وضبط المقاس */
        @page {{
            size: A4;
            margin: 0; /* إزالة هوامش المتصفح تماماً (يخفي التاريخ والرابط) */
        }}
        body {{
            margin: 0;
            padding: 0;
            background: #fff;
        }}
        #printableArea {{
            font-family: 'Cairo', sans-serif;
            direction: rtl;
            text-align: right;
            width: 100%;
            height: 100%;
            box-sizing: border-box; /* يضمن احتساب الهوامش داخل العرض */
            padding: 15mm; /* هامش داخلي آمن للطباعة */
            position: absolute;
            top: 0;
            left: 0;
        }}
        
        /* باقي التنسيقات */
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #2c3e50; padding-bottom: 10px; margin-bottom: 20px; }}
        .header img {{ height: 70px; object-fit: contain; }}
        .title-box {{ text-align: center; }}
        .title-box h1 {{ margin: 0; color: #2c3e50; font-size: 24px; font-weight: 800; }}
        .title-box p {{ margin: 0; color: #7f8c8d; font-size: 12px; }}
        
        .comp-code {{ background-color: #f1f2f6; color: #c0392b; padding: 5px 15px; border-radius: 15px; font-size: 1.1rem; font-weight: bold; margin-top: 8px; display: inline-block; border: 1px dashed #c0392b; }}
        
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; border: 1px solid #eee; padding: 15px; border-radius: 8px; }}
        .info-item {{ padding-bottom: 5px; border-bottom: 1px solid #f9f9f9; }}
        .label {{ font-weight: bold; color: #2980b9; font-size: 0.9rem; margin-left: 5px; }}
        .value {{ font-size: 1rem; font-weight: 600; color: #2c3e50; }}
        
        .section-title {{ background: #ecf0f1; color: #2c3e50; padding: 5px 10px; font-weight: 800; border-right: 4px solid #2980b9; margin: 20px 0 10px; font-size: 1.1rem; }}
        .desc-box {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #fafafa; min-height: 60px; line-height: 1.6; white-space: pre-wrap; font-size: 1rem; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; }}
        th {{ background: #2c3e50; color: white; text-align: right; padding: 8px; }}
        td {{ padding: 8px; border-bottom: 1px solid #eee; }}
        
        .footer {{ position: fixed; bottom: 10mm; left: 0; right: 0; text-align: center; font-size: 0.8rem; color: #aaa; border-top: 1px solid #eee; padding-top: 10px; }}
    </style>
    </head>
    <body>
        <div id="printableArea">
            <div class="header">
                <img src="data:image/png;base64,{b64_right}" alt="Logo">
                <div class="title-box">
                    <h1>نظام إدارة الشكاوى</h1>
                    <p>Unified Complaint Management System</p>
                    <div class="comp-code">رقم الشكوى: {comp.code}</div>
                </div>
                <img src="data:image/png;base64,{b64_left}" alt="Logo">
            </div>
            
            <div class="info-grid">
                <div class="info-item"><span class="label">اسم العميل:</span><span class="value">{comp.customer_name}</span></div>
                <div class="info-item"><span class="label">تاريخ الورود:</span><span class="value">{date_str}</span></div>
                <div class="info-item"><span class="label">رقم الهاتف:</span><span class="value">{comp.phone}</span></div>
                <div class="info-item"><span class="label">المصدر:</span><span class="value">{comp.source}</span></div>
                <div class="info-item"><span class="label">الإدارة المختصة:</span><span class="value">{comp.department.name}</span></div>
                <div class="info-item"><span class="label">المشروع:</span><span class="value">{comp.project.name}</span></div>
                <div class="info-item"><span class="label">الحالة الحالية:</span><span class="value">{status_arabic}</span></div>
            </div>
            
            <div class="section-title">📄 تفاصيل الشكوى</div>
            <div class="desc-box">{comp.description}</div>
            
            <div class="section-title">🕒 سجل المتابعة</div>
            <table>
                <thead><tr><th>التاريخ</th><th>المستخدم</th><th>الإجراء</th><th>التفاصيل</th></tr></thead>
                <tbody>{history_rows}</tbody>
            </table>
            
            <div class="footer">تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}</div>
        </div>
        <script>setTimeout(function() {{ window.print(); }}, 500);</script>
    </body>
    </html>
    """
    return html

# -----------------------------------------------------------------------------
# دالة تصميم إيصال العميل (A5) - للإيصال الفوري
# -----------------------------------------------------------------------------
def get_receipt_html(comp, logo_right_path, logo_left_path):
    import base64
    from datetime import datetime

    STATUS_AR = { "New": "جديد", "In Progress": "جاري التنفيذ", "Resolved": "تم الحل", "Closed": "مغلق", "All": "الكل" }
    status_arabic = STATUS_AR.get(comp.status, comp.status)

    def img_to_b64(path):
        try:
            with open(path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
        except: return ""

    b64_right = img_to_b64(logo_right_path)
    b64_left = img_to_b64(logo_left_path)
    date_str = comp.created_at.strftime("%Y-%m-%d %I:%M %p")

    html = f"""
    <html>
    <head>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        /* إزالة هوامش المتصفح للإيصال */
        @page {{
            size: A5 landscape; /* إيصال بالعرض */
            margin: 0; 
        }}
        body {{
            margin: 0;
            padding: 0;
            background: #fff;
        }}
        #receiptArea {{
            font-family: 'Cairo', sans-serif;
            direction: rtl;
            text-align: right;
            width: 100%;
            height: 100%;
            box-sizing: border-box;
            padding: 10mm; /* الهامش الداخلي الفعلي للإيصال */
            position: absolute;
            top: 0;
            left: 0;
        }}

        .receipt-border {{
            border: 2px dashed #333; /* الإطار المنقط داخل الهامش */
            padding: 15px;
            height: 90%; /* ارتفاع مناسب */
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        .header img {{ height: 50px; }}
        .header h2 {{ margin: 0; font-size: 1.4rem; color: #2c3e50; }}
        
        .big-code {{ text-align: center; background: #f0f3f4; padding: 10px; border-radius: 8px; margin: 10px 0; border: 1px solid #bdc3c7; }}
        .big-code span {{ display: block; font-size: 0.8rem; color: #7f8c8d; }}
        .big-code strong {{ display: block; font-size: 1.8rem; color: #c0392b; letter-spacing: 2px; }}

        .details-box {{ font-size: 0.95rem; margin-bottom: 10px; }}
        .line {{ display: flex; justify-content: space-between; border-bottom: 1px dotted #ccc; padding: 4px 0; }}
        .lbl {{ font-weight: bold; color: #2980b9; }}
        
        .instructions {{ background: #e8f8f5; padding: 8px; border-radius: 5px; font-size: 0.8rem; color: #0e6655; border: 1px solid #a2d9ce; }}
        .footer {{ text-align: center; font-size: 0.7rem; color: #aaa; margin-top: 5px; }}
    </style>
    </head>
    <body>
        <div id="receiptArea">
            <div class="receipt-border">
                <div class="header">
                    <img src="data:image/png;base64,{b64_right}" alt="Logo">
                    <div style="text-align:center">
                        <h2>إيصال استلام شكوى</h2>
                        <span style="font-size:0.8rem; color:#777">Complaint Receipt</span>
                    </div>
                    <img src="data:image/png;base64,{b64_left}" alt="Logo">
                </div>

                <div class="big-code">
                    <span>رقم الشكوى المرجعي</span>
                    <strong>{comp.code}</strong>
                </div>

                <div class="details-box">
                    <div class="line"><span class="lbl">العميل:</span> <span>{comp.customer_name}</span></div>
                    <div class="line"><span class="lbl">التاريخ:</span> <span>{date_str}</span></div>
                    <div class="line"><span class="lbl">الإدارة:</span> <span>{comp.department.name}</span></div>
                    <div class="line"><span class="lbl">الموضوع:</span> <span>{comp.description[:60]}...</span></div>
                </div>

                <div class="instructions">
                    <b>ℹ️ تنبيه هام:</b> يرجى الاحتفاظ بهذا الإيصال. سيتم الرد خلال 3 أيام عمل.
                </div>

                <div class="footer">تاريخ الطباعة: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}</div>
            </div>
        </div>
        <script>setTimeout(function() {{ window.print(); }}, 500);</script>
    </body>
    </html>
    """
    return html