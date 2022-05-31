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

from odoo import api, fields, models


####################
# Product Template #
####################
class ProductTemplate(models.Model):
    _inherit = "product.template"

    no_auto_reorder = fields.Boolean(
        string="Don't create reordering rules from templates",
        help="Do not create reordering rules automatically.\n"
        "You can create reordering rules later manually",
    )

    # -- Create or Update reordering rules (minimum inventory)
    def reorder_rules_update(self):
        """
        Automatically creates or updates existing reordering rules based on templates
        :return:
        """
        self.product_variant_ids.reorder_rules_update()

    # -- Write
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # Update reordering rules
        if "categ_id" in vals:
            self.product_variant_ids.reorder_rules_update()
        return res


###################
# Product Product #
###################
class ProductProduct(models.Model):
    _inherit = "product.product"

    # -- Create
    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if not res.no_auto_reorder:
            res.reorder_rules_update()
        return res

    # -- Write
    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        # Update reordering rules
        if "categ_id" in vals:
            self.filtered(lambda rec: rec.no_auto_reorder is False).with_context(
                {"del_existing": True, "attrs_only": False}
            ).reorder_rules_update()
        elif "attribute_value_ids" in vals:
            self.filtered(lambda rec: rec.no_auto_reorder is False).with_context(
                {"del_existing": True, "attrs_only": True}
            ).reorder_rules_update()
        return res

    # -- Create or Update reordering rules (minimum inventory)
    def reorder_rules_update(self):
        """
        Automatically creates or updates existing reordering rules based on templates
        :return:
        """

        # Check if attrs_only in vals.
        # Attrs are limited to Pro version so avoid excessive computations
        if self._context.get("attrs_only", False):
            return

        # Get global template. Use this template in no other found
        global_templates = self.env["cx.orderpoint.template"].search(
            [("category_id", "=", False)]
        )

        # Check if we need to delete existing reordering rules if no rule is found
        # This is used for "write" primary
        del_existing = self._context.get("del_existing", False)

        # Legacy. Get default company and location
        # in case not specified in template explicitly
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        if warehouse:
            warehouse_id = warehouse.id
            location_id = warehouse.lot_stock_id.id
        else:
            warehouse_id = False
            location_id = False

        for rec in self:
            # Applied only to stockable products
            if not rec.type == "product":
                continue

            # Check if auto creation is disabled
            if rec.no_auto_reorder:
                continue
            # Compose domain in case product is company related
            domain = [("category_id", "=", rec.categ_id.id)]
            if rec.company_id:
                domain.append(("company_id", "=", rec.company_id.id))

            # Product Category Based
            templates = self.env["cx.orderpoint.template"].search(domain)

            # Use global templates as fallback
            if not templates:
                if not global_templates:
                    if del_existing:
                        self.env["stock.warehouse.orderpoint"].search(
                            [
                                ("product_id", "=", rec.id),
                                ("template_control", "=", True),
                            ]
                        ).unlink()
                    continue
                # Fall back to global
                templates = global_templates

            # We can have multiple templates
            for template in templates:
                template_warehouse_id = (
                    template.warehouse_id.id if template.warehouse_id else warehouse_id
                )
                template_location_id = (
                    template.location_id.id if template.location_id else location_id
                )
                vals = {
                    "product_id": rec.id,
                    "template_id": template.id,
                    "product_min_qty": template.product_min_qty,
                    "product_max_qty": template.product_max_qty,
                    "qty_multiple": template.qty_multiple,
                    "group_id": template.group_id.id,
                    "warehouse_id": template_warehouse_id,
                    "location_id": template_location_id,
                }
                # Update existing reordering rules or create new
                existing_rules = self.env["stock.warehouse.orderpoint"].search(
                    [
                        ("product_id", "=", rec.id),
                        ("warehouse_id", "=", template_warehouse_id),
                        ("location_id", "=", template_location_id),
                    ]
                )
                if existing_rules:
                    existing_rules.write(vals)
                else:
                    vals.update(
                        {"template_control": True, "company_id": template.company_id.id}
                    )
                    self.env["stock.warehouse.orderpoint"].create(vals)
