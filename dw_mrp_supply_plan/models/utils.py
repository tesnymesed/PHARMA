def _domain_supply_products():
    return [
        ('product_tmpl_id.categ_id.is_final_product', '=', False),
        ('product_tmpl_id.categ_id.name', 'in', ['MP', 'AC']),
        ('product_tmpl_id.purchase_ok', '=', True),
    ]
