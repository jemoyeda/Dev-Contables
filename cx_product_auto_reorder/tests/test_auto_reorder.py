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

from odoo.tests import common


class TestAutoReorder(common.TransactionCase):
    def setUp(self):
        super(TestAutoReorder, self).setUp()
        self.orderpoint_template_model = self.env["cx.orderpoint.template"]
        self.product_category_model = self.env["product.category"]
        self.product_model = self.env["product.product"]

        self.rule_model = self.env["stock.warehouse.orderpoint"]

        self.category_1 = self.product_category_model.create({"name": "Category 1"})
        self.category_2 = self.product_category_model.create({"name": "Category 2"})

        self.product_1 = self.product_model.create(
            {
                "name": "Product 1",
                "type": "product",
                "categ_id": self.category_1.id,
            }
        )
        self.product_2 = self.product_model.create(
            {
                "name": "Product 2",
                "type": "product",
                "categ_id": self.category_1.id,
            }
        )

        self.template_1 = self.orderpoint_template_model.create(
            {
                "category_id": self.category_1.id,
                "product_min_qty": 5,
                "product_max_qty": 21,
                "company_id": 1,
                "warehouse_id": 1,
                "location_id": 1,
            }
        )

        self.template_2 = self.orderpoint_template_model.create(
            {
                "category_id": self.category_2.id,
                "product_min_qty": 1,
                "product_max_qty": 10,
                "company_id": 1,
                "warehouse_id": 1,
                "location_id": 1,
            }
        )

    def test_product_reordering_qty(self):
        """
        1.Checking to match qty of reordering product and reordering qty of template
        2.Checking to match product in template

        help: see blots '#' + number of checking
        """

        # 1
        self.assertEqual(
            self.template_1.product_min_qty,
            self.product_1.reordering_min_qty,
            msg="Product min qty must be equal to rule template min qty",
        )
        self.assertEqual(
            self.template_1.product_max_qty,
            self.product_1.reordering_max_qty,
            msg="Product max qty must be equal to rule template max qty",
        )
        # 2
        self.assertIn(
            self.product_1.id, self.template_1.rule_ids.mapped("product_id").ids
        )

    def test_count_orderpoint_template_rule(self):
        """
        Checking count of reordering rules
        """
        self.template_1.apply_template()
        self.assertEqual(
            self.template_1.rule_ids_count,
            2,
            msg="Number of rules must be 2",
        )

    def test_no_auto_reorder_product(self):
        """
        Checking no auto reorder field in product
        """
        self.product_3 = self.product_model.create(
            {
                "name": "Product 3",
                "type": "product",
                "categ_id": self.category_2.id,
                "no_auto_reorder": True,
            }
        )
        self.assertEqual(
            self.template_2.rule_ids_count, 0, msg="Number of rules must be 0"
        )

    def test_change_product_category(self):
        """
        Change product category and check rule changes
        """
        self.assertEqual(
            self.template_1.rule_ids_count,
            2,
            msg="Number of rules must be 2",
        )
        self.product_2.categ_id = self.category_2
        self.assertEqual(
            self.template_2.product_min_qty,
            self.product_2.reordering_min_qty,
            msg="Product min qty must be equal to rule template min qty",
        )
        self.assertEqual(
            self.template_2.product_max_qty,
            self.product_2.reordering_max_qty,
            msg="Product max qty be equal to rule template max qty",
        )
        self.assertEqual(
            self.template_2.rule_ids_count,
            1,
            msg="Number of rules must be 1",
        )

    def test_template_ids_in_rules(self):
        """
        Checking to match rules and template
        """
        product_3 = self.product_model.create(
            {
                "name": "Product 3",
                "type": "product",
                "categ_id": self.category_2.id,
            }
        )
        rule_1 = self.rule_model.create(
            {
                "product_id": product_3.id,
                "template_id": self.template_2.id,
                "product_min_qty": self.template_2.product_min_qty,
                "product_max_qty": self.template_2.product_max_qty,
                "qty_multiple": self.template_2.qty_multiple,
            }
        )
        self.assertIn(rule_1.id, self.template_2.rule_ids.ids)

    def test_template_control(self):
        """
        Check 'Template Control' setting
        """
        test_product = self.product_model.create(
            {
                "name": "Test Product",
                "type": "product",
                "categ_id": self.category_1.id,
            }
        )
        # test_template.rule_ids_count -> 3
        test_rule = self.rule_model.search([("product_id", "=", test_product.id)])
        # test_rule.template_control -> True
        self.assertTrue(
            test_rule.template_control, msg="Template control must be 'True'"
        )
        # changes to the template
        self.template_1.product_max_qty = 25
        # checking value in the rule
        self.assertEqual(
            test_rule.product_max_qty,
            self.template_1.product_max_qty,
            msg="Product max qty must be '25'",
        )
        # change template_control equal -> False
        test_rule.template_control = False
        # checking template_control value
        self.assertFalse(
            test_rule.template_control, msg="Template control must be 'False'"
        )
        # change template product_max_qty
        self.template_1.product_max_qty = 100
        # if template_control is false, product_max_qty will not change
        self.assertEqual(
            test_rule.product_max_qty,
            25.0,
            msg="Product max qty in rule must be '25'",
        )
