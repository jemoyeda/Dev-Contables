###################################################################################
# 
#    Copyright (C) Cetmix OÜ
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import _, api, fields, models
from odoo.osv import expression

TEMPLATE_FIELDS = [
    "product_min_qty",
    "product_max_qty",
    "qty_multiple",
    "group_id",
    "company_id",
    "warehouse_id",
    "location_id",
]


#######################
# Orderpoint Template #
#######################
class OrderpointTemplate(models.Model):
    _name = "cx.orderpoint.template"
    _description = "Minimum Inventory Rule Template"

    # -- Get template fields. Override to add custom fields
    def _get_template_fields(self):
        return TEMPLATE_FIELDS

    # Get default Warehouse and Location
    @api.model
    def default_get(self, fields):
        res = super(OrderpointTemplate, self).default_get(fields)
        warehouse = None
        if "warehouse_id" not in res and res.get("company_id"):
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", res["company_id"])], limit=1
            )
        if warehouse:
            res["warehouse_id"] = warehouse.id
            res["location_id"] = warehouse.lot_stock_id.id
        return res

    name = fields.Char(string="Name", compute="_compute_name", store=False)
    active = fields.Boolean(string="Active", default=True)
    category_id = fields.Many2one(
        string="Product Category",
        comodel_name="product.category",
        copy=False,
        ondelete="cascade",
    )
    attr_val_ids = fields.Many2many(
        string="Attribute Values",
        comodel_name="product.attribute.value",
        relation="cx_op_tpl_pr_attr_val_rel",
        column1="cx_op_template_id",
        column2="attr_val_id",
    )
    product_min_qty = fields.Float(
        string="Minimum Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    product_max_qty = fields.Float(
        string="Maximum Quantity",
        digits="Product Unit of Measure",
        required=True,
    )
    qty_multiple = fields.Float(
        string="Qty Multiple",
        digits="Product Unit of Measure",
        default=1,
        required=True,
    )
    group_id = fields.Many2one("procurement.group", "Procurement Group", copy=False)
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.user.company_id.id,
        copy=False,
    )
    warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
        ondelete="cascade",
        required=False,
        copy=False,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location",
        ondelete="cascade",
        required=False,
        copy=False,
    )
    rule_ids = fields.One2many(
        string="Related Rules",
        comodel_name="stock.warehouse.orderpoint",
        inverse_name="template_id",
    )
    rule_ids_count = fields.Integer(
        string="Rules Count", compute="_compute_rule_ids_count"
    )
    allowed_location_ids = fields.One2many(
        comodel_name="stock.location", compute="_compute_allowed_location_ids"
    )

    _sql_constraints = [
        (
            "tmpl_name_uniq",
            "unique(category_id, company_id)",
            "Such template already exists for this company!",
        )
    ]

    # -- Warehouse change
    @api.onchange("warehouse_id")
    def onchange_warehouse(self):
        for rec in self:
            if rec.warehouse_id:
                rec.location_id = rec.warehouse_id.lot_stock_id.id

    # -- Company change
    @api.onchange("company_id")
    def onchange_company_id(self):
        for rec in self:
            if rec.company_id:
                rec.warehouse_id = self.env["stock.warehouse"].search(
                    [("company_id", "=", rec.company_id.id)], limit=1
                )

    # -- Count related rules
    @api.depends("rule_ids")
    def _compute_rule_ids_count(self):
        for rec in self:
            rec.rule_ids_count = len(rec.rule_ids)

    # -- Compose name
    @api.depends("category_id")
    def _compute_name(self):
        for rec in self:
            prefix = rec.category_id.name_get()[0][1] if rec.category_id else False
            if prefix:
                rec.name = prefix
            else:
                rec.name = _("Global")

    # -- Compose name -- PRO
    @api.depends("category_id", "attr_val_ids")
    def _compute_name_pro(self):
        self.ensure_one()
        prefix = self.category_id.name if self.category_id else False
        suffix = (
            [attr_val_id.name for attr_val_id in self.attr_val_ids]
            if len(self.attr_val_ids) > 0
            else False
        )
        if not prefix and not suffix:
            self.name = False
        elif prefix and suffix:
            self.name = "{} > {}".format(prefix, suffix)
        elif prefix:
            self.name = prefix
        else:
            self.name = suffix

    # -- Get available locations. This is a copy of Odoo function
    @api.depends("warehouse_id")
    def _compute_allowed_location_ids(self):
        loc_domain = [("usage", "in", ("internal", "view"))]
        # We want to keep only the locations
        #  - strictly belonging to our warehouse
        #  - not belonging to any warehouses
        for orderpoint in self:
            other_warehouses = self.env["stock.warehouse"].search(
                [("id", "!=", orderpoint.warehouse_id.id)]
            )
            for view_location_id in other_warehouses.mapped("view_location_id"):
                loc_domain = expression.AND(
                    [loc_domain, ["!", ("id", "child_of", view_location_id.id)]]
                )
                loc_domain = expression.AND(
                    [
                        loc_domain,
                        [
                            "|",
                            ("company_id", "=", False),
                            ("company_id", "=", orderpoint.company_id.id),
                        ],
                    ]
                )
            orderpoint.allowed_location_ids = self.env["stock.location"].search(
                loc_domain
            )

    # -- Apply template
    def apply_template(self):
        # This is a legacy call for rules with no Warehouse or Location defined
        vals = self.default_get(["warehouse_id", "location_id"])
        warehouse_id = vals.get("warehouse_id", False)
        location_id = vals.get("location_id", False)
        for rec in self:
            is_global = False
            if rec.category_id:
                # Local templates
                products = self.env["product.product"].search(
                    [
                        ("categ_id", "=", rec.category_id.id),
                        ("type", "=", "product"),
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "=", rec.company_id.id),
                    ]
                )
            else:
                # Global template
                products = self.env["product.product"].search(
                    [
                        ("type", "=", "product"),
                        "|",
                        ("company_id", "=", False),
                        ("company_id", "=", rec.company_id.id),
                    ]
                )
                is_global = True

            # Apply template to products
            for product in products:
                # Get existing rules
                existing_rules = self.env["stock.warehouse.orderpoint"].search(
                    [
                        ("product_id", "=", product.id),
                        (
                            "warehouse_id",
                            "=",
                            rec.warehouse_id.id if rec.warehouse_id else warehouse_id,
                        ),
                        (
                            "location_id",
                            "=",
                            rec.location_id.id if rec.location_id else location_id,
                        ),
                    ]
                )
                len_existing_rules = len(existing_rules)

                # Do not apply Global template if rules exist
                if (
                    is_global
                    and len_existing_rules > 0
                    and len(existing_rules.filtered(lambda t: not t.template_id)) == 0
                ):
                    continue

                vals = {
                    "product_id": product.id,
                    "template_id": rec.id,
                    "product_min_qty": rec.product_min_qty,
                    "product_max_qty": rec.product_max_qty,
                    "qty_multiple": rec.qty_multiple,
                    "group_id": rec.group_id.id,
                    "warehouse_id": rec.warehouse_id.id
                    if rec.warehouse_id
                    else warehouse_id,
                    "location_id": rec.location_id.id
                    if rec.location_id
                    else location_id,
                }

                # Update existing reordering rules or create new
                if len_existing_rules > 0:
                    existing_rules.write(vals)
                else:
                    vals.update({"template_control": True})
                    self.env["stock.warehouse.orderpoint"].create(vals)

    # -- Create
    @api.model
    def create(self, vals):
        res = super(OrderpointTemplate, self).create(vals)
        res.apply_template()
        return res

    # -- Write
    def write(self, vals):

        # Remove category and attribute values
        vals.pop("category_id", False)
        vals.pop("attr_val_ids", False)

        # Write
        res = super(OrderpointTemplate, self).write(vals)

        # Get new vals for rules
        rule_vals = {}

        template_keys = self._get_template_fields()
        for key in template_keys:
            if key in vals:
                rule_vals.update({key: vals.get(key, False)})

        # Update all related rules
        if len(rule_vals) > 0:
            self.env["stock.warehouse.orderpoint"].search(
                [("template_id", "in", self.ids), ("template_control", "=", True)]
            ).write(rule_vals)

        return res

    # -- Delete
    def unlink(self):

        # Get products
        product_ids = self.mapped("rule_ids").mapped("product_id")

        # Delete templates
        res = super(OrderpointTemplate, self).unlink()

        # Re-apply template
        if len(product_ids) > 0:
            product_ids.reorder_rules_update()

        return res


##########################
# Minimum Inventory Rule #
##########################
class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    template_id = fields.Many2one(
        string="Template",
        comodel_name="cx.orderpoint.template",
        ondelete="set null",
        auto_join=True,
    )
    template_control = fields.Boolean(
        string="Control via Template",
        help="Modify rule automatically when template is modified\n",
    )
