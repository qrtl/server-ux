# Migrated to v14.0 by Ashish Hirpara (https://www.ashish-hirpara.com)
# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class IrFilters(models.Model):
    _inherit = "ir.filters"
    _order = "model_id, sequence, name, id desc"

    def _selection_type(self):
        return [
            ("favorite", "Favorite"),
            ("search", "Search"),
            ("filter", "Standard Filter"),
            ("groupby", "Standard Group By"),
        ]

    sequence = fields.Integer()
    type = fields.Selection(
        selection="_selection_type",
        required=True,
        default="favorite",
    )
    search_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        ondelete="cascade",
    )
    groupby_field = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Group By Field",
        ondelete="cascade",
    )
    filter_domain = fields.Text(
        help="""Enter a filter domain expression if necessary.
        Example: [('default_code', 'ilike', self)]"""
    )
    date_field = fields.Many2one(
        comodel_name="ir.model.fields",
        ondelete="cascade",
        domain="[('model', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help="If set, creates a date filter with period options "
        "(Today, This Week, This Month, etc.) instead of a domain filter. "
        "Only applicable for filter type.",
    )
    group_ids = fields.Many2many("res.groups", string="User Groups")
    group_id = fields.Many2one(comodel_name="ir.filters.group", string="Filter Group")

    @api.constrains("type", "domain", "date_field")
    def _check_filter_type_fields(self):
        for record in self:
            if record.type != "filter":
                continue
            has_domain = record.domain and record.domain != "[]"
            if has_domain and record.date_field:
                raise ValidationError(
                    _(
                        "Filter '%(name)s': You cannot set both Domain and "
                        "Date Field. Please choose only one.",
                        name=record.name,
                    )
                )
            if not has_domain and not record.date_field:
                raise ValidationError(
                    _(
                        "Filter '%(name)s': You must set either Domain or "
                        "Date Field for filter type.",
                        name=record.name,
                    )
                )

    @api.onchange("type")
    def _onchange_type_clear_date_field(self):
        if self.type != "filter":
            self.date_field = False

    @api.onchange("domain")
    def _onchange_domain_clear_date_field(self):
        if self.domain and self.domain != "[]" and self.date_field:
            self.date_field = False

    @api.onchange("date_field")
    def _onchange_date_field_clear_domain(self):
        if self.date_field:
            self.domain = "[]"

    @api.model
    def get_filters(
        self,
        model,
        action_id=None,
        embedded_action_id=None,
        embedded_parent_res_id=None,
    ):
        """We need to inject a context to obtain only the records of favorite type."""
        self = self.with_context(filter_type="favorite")
        return super().get_filters(
            model, action_id, embedded_action_id, embedded_parent_res_id
        )

    @api.model
    @api.returns("self")
    def search(self, domain, offset=0, limit=None, order=None):
        if self.env.context.get("filter_type"):
            domain = expression.AND(
                (domain, [("type", "=", self.env.context["filter_type"])])
            )
        return super().search(domain, offset, limit, order)
