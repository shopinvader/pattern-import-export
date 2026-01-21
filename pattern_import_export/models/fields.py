# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields

ori_write_real = fields.One2many.write_real


def write_real(self, records_commands_list, create=False):
    if not create:
        for recs, commands in records_commands_list:
            if recs.env.context.get("pattern_config", {}).get("purge_one2many"):
                update_ids = [cmd[1] for cmd in commands if cmd[0] == 1]
                for item in recs[self.name]:
                    if item.id not in update_ids:
                        commands.append((3, item.id, 0))
    return ori_write_real(self, records_commands_list, create=create)


fields.One2many.write_real = write_real
