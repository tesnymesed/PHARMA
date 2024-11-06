def _domain_pf_products():
    return [
        ('product_tmpl_id.type', '=', 'product'),
        ('product_tmpl_id.categ_id.is_final_product', '=', True),
        # ('product_tmpl_id.bom_ids', '!=', False)
        # ('product_tmpl_id.company_id', '=', company_id),
    ]

    # return [('product_tmpl_id.categ_id.is_final_product', '=', True), ('product_tmpl_id.bom_ids', '!=', False)]
