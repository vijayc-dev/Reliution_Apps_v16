{
    'name': 'RCS Inventory and Invoice Catalog',
    'author': 'vijay Reliution',
    'description': 'RCS Catalog',
    'license': 'LGPL-3',

    'application': True,
    'installable': True,
    'version': '16.0.0.1',

    'depends': ['base', 'sale', 'product', 'web','stock','purchase'],

    'data': [
        'views/product_catalog_view.xml',
        'views/sale_catalog_view.xml',
        'views/purchase_catalog_view.xml',
        'views/inventory_catalog_view.xml',
        'views/invoice_catalog_view.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_view.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/order_line/order_line.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_controller.xml',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_controller.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_model.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_renderer.xml',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_renderer.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_record.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/kanban_record.xml',
            # 'rcs_inventory_and_invoice_catalog/static/src/product_catalog/search/search_panel.xml',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/search/search_panel.js',
            'rcs_inventory_and_invoice_catalog/static/src/product_catalog/catalog_css.css'
        ],
    },
}
