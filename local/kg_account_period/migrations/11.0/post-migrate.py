

def migrate(cr, version):
    if version == '11.0.0.0.2':
        # update blank company id
        cr.execute("""update invoice_collecting set company_id = s.company_id
        FROM (
         SELECT distinct c.id, i.company_id
         FROM invoice_collecting c 
         left join invoice_collecting_line l on l.invoice_collecting_id = c.id
            left join account_invoice i on i.id = l.invoice_id
            where i.company_id is null) s
        where invoice_collecting.id = s.id
        and invoice_collecting.company_id is null
        """)
        # Drop temporary column example
        # cr.execute('ALTER TABLE product_template DROP COLUMN temporary_credit_product')
